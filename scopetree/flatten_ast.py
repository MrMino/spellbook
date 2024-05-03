"""
Flattens AST tree into a well-ordered list of nodes. Only expressions and
statements are present in the list.

Nodes listed earlier have line numbers lower than those that follow.
"""

from __future__ import annotations

import ast
import sys
from pprint import pprint


def flatten_ast(tree: ast.AST):
    nodes = [node for node in ast.walk(tree) if isinstance(node, (ast.stmt, ast.expr))]
    return sorted(nodes, key=lambda n: n.lineno)


USAGE = f"Usage: {sys.argv[0]} <path>"
MAXARGS = 2
MINARGS = 2


def main(args: list[str]):
    path = args[0]
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    ast_tree = ast.parse(code)
    pprint(flatten_ast(ast_tree))


if __name__ == "__main__":
    if not (MINARGS <= len(sys.argv) <= MAXARGS):
        print(USAGE)
        sys.exit(1)

    sys.argv.pop(0)
    main(sys.argv)
