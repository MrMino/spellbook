"""
Generates a tree of scopes present in the code, including scopes shadowed by
using the same name.
"""

from __future__ import annotations

import symtable
import sys
import textwrap


class ScopeTreeNode:
    def __init__(
        self,
        symbols: symtable.SymbolTable,
        parent: ScopeTreeNode | None,
    ) -> None:
        self.symbols = symbols
        self.children = []
        self.child_names = []
        self.parent = parent

        # The children symbol tables aren't necessarily ordered by their line numbers.
        # Consider the following code:
        #
        #     @lambda func: None
        #     def same_lineno() -> lambda: None:
        #         pass
        #
        # The decorator lambda will come after the returntype lambda.
        children = sorted(symbols.get_children(), key=lambda s: s.get_lineno())

        for child in children:
            new_node = ScopeTreeNode(child, self)
            self.children.append(new_node)
            self.child_names.append(new_node.name)

    def __str__(self):
        return f"{self.kind} {self.qualname} (line {self.lineno})"

    @property
    def name(self) -> str:
        return self.symbols.get_name()

    @property
    def qualname(self) -> str:
        return self.parent.qualname + "." + self.name if self.parent is not None else ""

    @property
    def kind(self) -> str:
        return self.symbols.get_type()

    @property
    def lineno(self) -> int:
        return self.symbols.get_lineno()

    def tree_str(self) -> str:
        tree_str = ""
        for child_idx, child in enumerate(self.children):
            tree_str += f"\n{child_idx}: {child.tree_str()}"

        tree_str = textwrap.indent(tree_str, "    ")
        return f"{self!s}" + tree_str


class ScopeTreeRoot(ScopeTreeNode):
    def __init__(self, symbols: symtable.SymbolTable, path: str | None = None) -> None:
        if path is None:
            path = "<unnamed module>"
        self.path = path

        super().__init__(symbols, None)

    def __str__(self):
        return f"Global scope ({self.path})"

    @property
    def name(self) -> str:
        return "."

    @classmethod
    def from_file(cls, path: str) -> ScopeTreeRoot:
        with open(path, "r", encoding="utf-8") as f:
            symbols = symtable.symtable(f.read(), path, "exec")
        return ScopeTreeRoot(symbols, path)


USAGE = f"Usage: {sys.argv[0]} <path>"
MAXARGS = 2
MINARGS = 2


def main(args: list[str]):
    path = args[0]
    print(ScopeTreeRoot.from_file(path).tree_str())


if __name__ == "__main__":
    if not (MINARGS <= len(sys.argv) <= MAXARGS):
        print(USAGE)
        sys.exit(1)

    sys.argv.pop(0)
    main(sys.argv)
