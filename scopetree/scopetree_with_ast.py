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

SCOPE_GENERATING = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


class ScopeTreeNode:
    def __init__(
        self,
        symbols: symtable.SymbolTable,
        ast_node: ast.AST,
        parent: ScopeTreeNode | None,
    ) -> None:
        self.symbols = symbols
        self.children = []
        self.child_names = []
        self.parent = parent
        self.ast_node = ast_node

        # The children symbol tables aren't necessarily ordered by their line numbers.
        # Consider the following code:
        #
        #     @lambda func: None
        #     def same_lineno() -> lambda: None:
        #         pass
        #
        # The decorator lambda will come after the returntype lambda.
        children = sorted(symbols.get_children(), key=lambda s: s.get_lineno())
        child_linenos = [table.get_lineno() for table in children]
        ast_nodes = [
            node for node in flatten_ast(ast_node) if isinstance(node, SCOPE_GENERATING)
        ]
        ast_linenos = [node.lineno for node in ast_nodes]

        scope_to_ast = {}
        iter_ast_linenos = iter(zip(ast_nodes, ast_linenos))

        for child, child_lineno, (ast_node, ast_lineno) in zip(
            children, child_linenos, iter_ast_linenos
        ):
            while child_lineno != ast_lineno:
                ast_node, ast_lineno = next(iter_ast_linenos)
            scope_to_ast[child] = ast_node

        for child, ast_node in scope_to_ast.items():
            new_node = ScopeTreeNode(child, ast_node, self)
            self.children.append(new_node)
            self.child_names.append(new_node.name)

    def __str__(self):
        symbols = self.symbols.get_symbols()
        return f"{self.kind} {self.qualname} (line {self.lineno}, ast {self.ast_node}) {symbols}"

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

        super().__init__(symbols, ast_tree, None)

    def __str__(self):
        return f"Global scope ({self.path})"

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
