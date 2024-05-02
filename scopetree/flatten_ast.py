"""
Flattens AST tree into a well-ordered list of nodes. Only expressions and
statements are present in the list.

Nodes listed earlier have line numbers lower than those that follow.
"""

import ast


def flatten_ast(tree: ast.AST):
    nodes = [node for node in ast.walk(tree) if isinstance(node, (ast.stmt, ast.expr))]
    return sorted(nodes, key=lambda n: n.lineno)
