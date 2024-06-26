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


def scope_traverse(scope_tree_root: ScopeTreeRoot, scope_path: str) -> ScopeTreeNode:
    if scope_path == ".":
        return scope_tree_root

    next_node: ScopeTreeNode = scope_tree_root
    for idx in (int(num) for num in scope_path.split(".")):
        next_node = next_node.children[idx]

    return next_node


USAGE = f"""\
Usage: {sys.argv[0]} <path> <scope> <symbol>"

You can specify a scope using indexes from ScopeTreeRoot, e.g. "1.2.3.4" or "."
to get the global scope.
"""
MAXARGS = 4
MINARGS = 4
ANSII_BOLD_YELLOW = "\033[1;31m"
ANSII_RESET = "\033[0m"


def main(args: list[str]):
    path, scope_path, symbol_name = args

    scope_tree = ScopeTreeRoot.from_file(path)
    target_scope = scope_traverse(scope_tree, scope_path)

    symbol = target_scope.symbols.lookup(symbol_name)
    print(symbol_summary(symbol))

    ast_nodes = flatten_ast(target_scope.ast_node)
    lines = [
        node.lineno
        for node in ast_nodes
        if hasattr(node, "id") and node.id == symbol_name
    ]

    print()
    print(f"{symbol_name!r} usage in {path}:")

    for lineno in lines:
        line = linecache.getline(path, lineno)
        line = line.lstrip()
        line = re.sub(
            rf"\b{symbol_name}\b",
            f"{ANSII_BOLD_YELLOW}{symbol_name}{ANSII_RESET}",
            line,
            count=1,
        )

        print(f"At line {lineno}:\n\t{line}")


if __name__ == "__main__":
    if not (MINARGS <= len(sys.argv) <= MAXARGS):
        print(USAGE)
        sys.exit(1)

    sys.argv.pop(0)
    main(sys.argv)
