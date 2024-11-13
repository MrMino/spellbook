# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "libcst==1.5.0",
# ]
# ///
"""
Modify imports in a file.
"""
from __future__ import annotations

import fnmatch
import re
import sys
import textwrap
from collections import namedtuple
from pathlib import Path

import libcst as cst
from libcst.helpers import get_full_name_for_node
from libcst.metadata import PositionProvider

ImportInfo = namedtuple("ImportInfo", "node, import_path, lineno")


def get_from_import_name(node: cst.ImportFrom) -> str:
    if node.module is not None:
        from_import_name = get_full_name_for_node(node.module)
        assert isinstance(from_import_name, str)
        dots = "." * len(node.relative)
        from_import_name = dots + from_import_name
    else:
        from_import_name = "."
    return from_import_name


class ImportCollector(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, pattern: str | None = None):
        if pattern is None:
            self.pattern = "*"
            self.skip_relative = False
            self.skip_non_relative = False
        else:
            self.pattern = pattern.lstrip(".")
            is_relative_pattern = pattern.startswith(".")
            self.skip_relative = not is_relative_pattern
            self.skip_non_relative = is_relative_pattern

        self.imports: list[ImportInfo] = []

    def _ln(self, node: cst.CSTNode) -> int:
        """Return a lineno of the node."""
        pos_info = self.get_metadata(PositionProvider, node)
        lineno = pos_info.start.line  # type: ignore
        assert isinstance(lineno, int)
        return lineno

    def visit_Import(self, node: cst.Import) -> None:
        for alias in node.names:
            import_name = get_full_name_for_node(alias.name)
            assert import_name is not None

            # Normal imports cannot be relative.
            if self.skip_non_relative:
                return

            if fnmatch.fnmatch(import_name, self.pattern):
                self.imports.append(ImportInfo(node, import_name, self._ln(alias)))

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        from_import_name = get_from_import_name(node)

        relative_node = node.relative or node.module is None
        if self.skip_relative and relative_node:
            return
        if self.skip_non_relative and not relative_node:
            return

        if not fnmatch.fnmatch(from_import_name, self.pattern):
            return

        self.imports.append(ImportInfo(node, from_import_name, self._ln(node)))


class ImportReplacer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, import_pattern: str, replace_with: str):
        # Check if pattern points at relative imports
        self.relative = import_pattern.startswith(".")
        self.pattern = import_pattern.lstrip(".")
        self.replace_with = replace_with

        self.pattern_ends_with_wildcard = import_pattern.endswith(".*")
        if self.pattern_ends_with_wildcard:
            self.regex = self._translate_pattern_to_regex(import_pattern)
        else:
            self.regex = None

    @staticmethod
    def _translate_pattern_to_regex(import_pattern):
        assert import_pattern.endswith(".*")
        # A .* wildcard has been used at the end.
        # We need to put the wildcard in a capture group. Edit the regex pattern.
        regex_pat = fnmatch.translate(import_pattern)
        # Replaces the _last_ occurence of ".*".
        regex_pat = r"(.*)".join(regex_pat.rsplit(".*", 1))
        regex = re.compile(regex_pat)
        return regex

    def _replaced_import_name(self, import_path: str) -> str:
        if not self.pattern_ends_with_wildcard:
            return self.replace_with
        assert self.regex is not None

        match = self.regex.match(import_path)
        assert match is not None
        tail = match.groups()[-1]
        return self.replace_with + "." + tail

    def _ln(self, node: cst.CSTNode) -> int:
        """Return a lineno of the node."""
        pos_info = self.get_metadata(PositionProvider, node)
        lineno = pos_info.start.line  # type: ignore
        assert isinstance(lineno, int)
        return lineno

    def leave_Import(self, node, updated_node):
        # Multiple modules may be imported in a single import statement.
        for alias in node.names:
            import_name = get_full_name_for_node(alias.name)
            assert import_name is not None

            # Normal imports cannot be relative.
            if self.relative:
                print(
                    f"Skipping non-relative import on line {self._ln(node)}: {import_name!r}"
                )
                return node
            if self.replace_with.startswith("."):
                print(
                    f"Skipping normal import on line {self._ln(node)}: {import_name!r} "
                    f" - replacement starts with a dot"
                )
                return node

            if fnmatch.fnmatch(import_name, self.pattern):
                old_name = import_name
                new_name = self._replaced_import_name(import_name)
                print(
                    f"Replacing import on line {self._ln(alias)}: {old_name!r} → {new_name!r}"
                )
                node = node.with_deep_changes(alias, name=new_full_name(new_name))
            else:
                print(
                    f"Skipping import on line {self._ln(alias)}: {import_name!r} - no match"
                )
        return node

    def leave_ImportFrom(self, node, updated_node):
        from_import_name = get_from_import_name(node)

        relative_node = node.relative or node.module is None
        if not self.relative and relative_node:
            print(
                f"Skipping relative from-import on line {self._ln(node)}: {from_import_name!r}"
            )
            return node
        if self.relative and not relative_node:
            print(
                f"Skipping non-relative from-import on line {self._ln(node)}: {from_import_name!r}"
            )
            return node

        if not fnmatch.fnmatch(from_import_name, import_pattern):
            print(
                f"Skipping import on line {self._ln(node)}: {from_import_name!r} - no match"
            )
            return node

        old_name = from_import_name
        new_name = self._replaced_import_name(from_import_name)
        print(
            f"Replacing from-import on line {self._ln(node)}: {old_name!r} → {new_name!r}"
        )

        # How many dots in the beginning of the new name?
        new_relative_level = len(new_name) - len(new_name.lstrip("."))

        node = node.with_changes(
            module=new_full_name(new_name),
            relative=[cst.Dot()] * new_relative_level,
        )

        return node


def new_full_name(dotted_name: str) -> cst.Attribute | cst.Name:
    dotted_name = dotted_name.lstrip(".")
    if "." not in dotted_name:
        return cst.Name(dotted_name)
    head, tail = dotted_name.rsplit(".", maxsplit=1)
    return cst.Attribute(new_full_name(head), cst.Name(tail))


def print_import_infos(imports: list[ImportInfo]):
    for _, import_path, lineno in imports:
        print(f"L{lineno}:\t{import_path}")


if __name__ == "__main__":
    arglen = len(sys.argv)
    if arglen == 1 or arglen > 4:
        print(
            textwrap.dedent(
                f"""\
        Usage: {sys.argv[0]} <path> [pattern] [replace_with]")

        - Given neither pattern nor replace_with, show all import paths and exit.
        - Given pattern without replace_with, show all imports matching the given
          pattern.
        - With both pattern and replace_with, replace import paths matching 
          pattern with replace_with.

        Pattern can use wildcards. For possible wildcards, see python docs of
        fnmatch.fnmatch().

        If wildcards are used within the pattern, the part of the import matching
        the last '.*' wildcard will be appended to the import after replacing.

        If pattern starts with a dot, only relative imports will be considered
        for replacement. When an import matches, the replacement text will be
        prepended to the import path."""
            )
        )
        sys.exit(1)

    path = Path(sys.argv[1])
    code = path.read_text()
    module = cst.parse_module(code)
    wrapper = cst.MetadataWrapper(module)

    if arglen == 2:
        collector = ImportCollector()
        wrapper.visit(collector)
        print_import_infos(collector.imports)
        sys.exit(0)

    import_pattern = sys.argv[2]

    if arglen == 3:
        collector = ImportCollector(import_pattern)
        wrapper.visit(collector)
        print_import_infos(collector.imports)
        sys.exit(0)

    elif arglen == 4:

        new_import_path = sys.argv[3]

        # if import_pattern.startswith("."):
        #     print("Error: relative imports are not supported yet.")
        #     sys.exit(1)

        modified_tree = wrapper.visit(ImportReplacer(import_pattern, new_import_path))
        new_code = modified_tree.code
        path.write_text(new_code)
