"""
Generates a tree of scopes present in the code, including scopes shadowed by
using the same name.

This version adds AST node information to each found scope. This depends on the
fact that the child tables returned by the symtable nodes are ordered in the
same way as the AST nodes used to create them.
"""

from __future__ import annotations

import ast
import symtable
import sys
import textwrap

from flatten_ast import flatten_ast

EXPR_NAMES = (
    "lambda",
    "listcomp",
    "setcomp",
    "dictcomp",
    "genexpr",
)

SCOPED_EXPR = (
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)

SCOPED_STMT = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
)


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
        self.ast_node: ast.AST = None  # Assigned by ScopeTreeRoot

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
        symbols = self.symbols.get_symbols()
        ast = (
            f"ast {self.ast_node.__class__.__name__} lineno {self.ast_node.lineno}"
            if self.ast_node is not None
            else "no ast"
        )
        return f"{self.kind} {self.qualname} (line {self.lineno}, {ast}) {symbols}"

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
    def __init__(
        self,
        symbols: symtable.SymbolTable,
        ast_tree: ast.AST,
        path: str | None = None,
    ) -> None:
        if path is None:
            path = "<unnamed module>"
        self.path = path

        super().__init__(symbols, None)

        self._find_ast_nodes(ast_tree)

    def __str__(self):
        return f"Global scope ({self.path})"

    def _find_ast_nodes(self, ast_tree) -> None:
        # Since scoped expressions violate the ordering between symtable
        # and ast, we need to take care of them separately.
        all_nodes = flatten_ast(ast_tree)

        # Take care of functions and classes first:
        stmt_children = filter(lambda child: child.name not in EXPR_NAMES, self.walk())
        stmt_nodes = [
            node for node in all_nodes if isinstance(node, SCOPED_STMT)
        ]

        for stmt_child, stmt_ast_node in zip(stmt_children, stmt_nodes):
            stmt_child.ast_node = stmt_ast_node

        # Then find ast nodes for the expression scopes:
        expr_children = filter(lambda child: child.name in EXPR_NAMES, self.walk())
        expr_nodes = [
            node for node in all_nodes if isinstance(node, SCOPED_EXPR)
        ]
        for expr_child, expr_ast_node in zip(expr_children, expr_nodes):
            expr_child.ast_node = expr_ast_node

    def walk(self):
        """Iterate over the subtree nodes.

        Returns the subtree's nodes excluding this one, in the order of their linenos.
        """
        stack = [*(reversed(self.children))]
        while stack:
            node = stack.pop()
            yield node
            stack.extend(reversed(node.children))

    @property
    def name(self) -> str:
        return "."

    @classmethod
    def from_file(cls, path: str) -> ScopeTreeRoot:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()
        symbols = symtable.symtable(code, path, "exec")
        ast_tree = ast.parse(code)
        return ScopeTreeRoot(symbols, ast_tree, path)


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
