from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ..nodes.base import DocstringNode
from ..nodes.function import FunctionDocstringNode

if TYPE_CHECKING:
    from ..converters import DocstringConverter


class DocstringVisitor(ast.NodeVisitor):
    def __init__(
        self, filename: str, converter: type[DocstringConverter] | None = None
    ) -> None:
        self.source_file: Path = Path(filename).expanduser().resolve()
        self.source_code: str = self.source_file.read_text()
        self.tree: ast.Module = ast.parse(self.source_code)

        self.docstrings_inspected: int = 0
        self.missing_docstrings: list[DocstringNode] = []

        self.module_name: str = self.source_file.stem
        self.stack: list[DocstringNode] = []

        self.docstring_converter: DocstringConverter | None = (
            converter(quote=not issubclass(self.__class__, ast.NodeTransformer))
            if converter
            else None
        )

    def report_missing_docstrings(self) -> None:
        if not self.missing_docstrings:
            print(f'No missing docstrings found in {self.source_file}.')
        else:
            for docstring_node in self.missing_docstrings:
                # TODO: need to print full path for node name
                print(
                    f'{docstring_node.fully_qualified_name} is missing a docstring',
                    file=sys.stderr,
                )
                self.handle_missing_docstring(docstring_node)

    def handle_missing_docstring(self, docstring_node: DocstringNode) -> DocstringNode:
        if self.docstring_converter:
            print('Hint:')
            print(self.docstring_converter.suggest_docstring(docstring_node))
            print()

    def process_docstring(self, docstring_node: DocstringNode) -> DocstringNode:
        if docstring_node.docstring is None or docstring_node.docstring.strip() == '':
            self.missing_docstrings.append(docstring_node)

        self.docstrings_inspected += 1
        return docstring_node

    def visit_docstring(
        self,
        node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module,
        docstring_class: type[DocstringNode],
    ) -> ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module:
        docstring_node = docstring_class(
            node,
            self.module_name,
            self.source_code,
            parent=self.stack[-1] if self.stack else None,
        )

        self.stack.append(docstring_node)  # TODO: call it docstringify_node?

        docstring_node = self.process_docstring(
            docstring_node
        )  # TODO: shouldn't require docstring if typing.overload decorator is there
        self.generic_visit(docstring_node.node)
        self.stack.pop()
        return docstring_node.node

    def visit_Module(self, node: ast.Module) -> ast.Module:  # noqa: N802
        return self.visit_docstring(node, DocstringNode)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:  # noqa: N802
        return self.visit_docstring(node, DocstringNode)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:  # noqa: N802
        return self.visit_docstring(node, FunctionDocstringNode)

    def visit_AsyncFunctionDef(  # noqa: N802
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        return self.visit_docstring(node, FunctionDocstringNode)

    def visit_Return(self, node: ast.Return) -> ast.Return:  # noqa: N802
        if isinstance(self.stack[-1], FunctionDocstringNode):
            self.stack[-1].return_statements.append(node)
        return node

    def process_file(self) -> None:
        self.visit(self.tree)
        self.report_missing_docstrings()
