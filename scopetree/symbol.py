#!/bin/env python
"""
Given a file, scope, and a symbol name, finds all usage of the specified symbol
in the scope.
"""

from __future__ import annotations

import linecache
import re
import sys
from symtable import Symbol

from flatten_ast import flatten_ast
from scopetree_with_ast import ScopeTreeNode, ScopeTreeRoot

SYMBOL_ATTRS = sorted(
    attr_name for attr_name in dir(Symbol) if attr_name.startswith("is_")
)


def symbol_summary(symbol: Symbol) -> str:
    name = symbol.get_name()
    true_attributes = [name for name in SYMBOL_ATTRS if getattr(symbol, name)()]

    return f"Symbol {repr(name)}: " + ", ".join(
        name.removeprefix("is_") for name in true_attributes
    )


def scope_traverse(
    scope_tree_root: ScopeTreeRoot, scope_path: str
) -> ScopeTreeNode | None:
    if scope_path == ".":
        return scope_tree_root

    segments = scope_path.split(".")

    next_node: ScopeTreeNode | None = scope_tree_root
    for segment in segments:
        if next_node is None:
            return None
        next_node = find_subscope(next_node, segment)

    return next_node


def find_subscope(scope: ScopeTreeNode, scope_id: str) -> ScopeTreeNode | None:
    try:
        scope_idx = int(scope_id)
    except ValueError:  # Not an integer id
        try:
            scope_idx = scope.child_names.index(scope_id)
        except ValueError:  # Not found
            return None
    return scope.children[scope_idx]


USAGE = f"""\
Usage: {sys.argv[0]} <path> <scope> <symbol>"

You can specify a scope using indexes from ScopeTreeRoot, e.g. "1.2.3.4"
or using the scope names, e.g. "1.2.class.func"
or "." to get the global scope.
"""
MAXARGS = 4
MINARGS = 4
ANSI_BOLD_YELLOW = "\033[1;31m"
ANSI_RESET = "\033[0m"
ANSI_GREY = "\033[90m"


def main(args: list[str]):
    exec, path, scope_path, symbol_name = args

    exec = exec.removeprefix("./")

    scope_tree = ScopeTreeRoot.from_file(path)
    target_scope = scope_traverse(scope_tree, scope_path)

    if target_scope is None:
        print(f"Scope not found: {scope_path!r}")
        sys.exit(1)

    ast_nodes = flatten_ast(target_scope.ast_node)
    lines = [
        node.lineno
        for node in ast_nodes
        if (
            hasattr(node, "id")
            and node.id == symbol_name
            or hasattr(node, "arg")
            and node.arg == symbol_name
        )
    ]

    if exec == "symbol_usage":
        symbol = target_scope.symbols.lookup(symbol_name)
        print(symbol_summary(symbol))

        print()
        print(f"{symbol_name!r} usage in {path}:")

        for lineno in lines:
            line = linecache.getline(path, lineno)
            line = line.lstrip()
            line = re.sub(
                rf"\b{symbol_name}\b",
                f"{ANSI_BOLD_YELLOW}{symbol_name}{ANSI_RESET}",
                line,
                count=1,
            )

            print(f"At line {lineno}:\n\t{line}")

    elif exec == "symbol_code":
        ruler_width = len(str(max(lines)))

        for lineno in lines:
            line = linecache.getline(path, lineno)
            line = re.sub(
                rf"\b{symbol_name}\b",
                f"{ANSI_BOLD_YELLOW}{symbol_name}{ANSI_RESET}",
                line,
                count=1,
            )

            if sys.stdout.isatty():
                print(f"{ANSI_GREY}{lineno:>{ruler_width}}{ANSI_RESET} {line}", end="")
            else:
                print(line, end="")


if __name__ == "__main__":
    if not (MINARGS <= len(sys.argv) <= MAXARGS):
        print(USAGE, end="")
        sys.exit(1)

    main(sys.argv)
