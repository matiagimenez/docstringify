from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from .docstring_generator import DocstringGenerator

if TYPE_CHECKING:
    from .converters import DocstringConverter


class DocstringVisitor(ast.NodeVisitor):
    def __init__(
        self, filename: str, converter: DocstringConverter | None = None
    ) -> None:
        self.source_file: Path = Path(filename).expanduser().resolve()
        self.source_code: str = self.source_file.read_text()
        self.tree: ast.Module = ast.parse(self.source_code)

        self.docstrings_inspected: int = 0
        self.missing_docstrings: int = 0

        self.module_name: str = self.source_file.stem
        self.stack: list[str] = []

        self.docstring_generator: DocstringGenerator | None = (
            DocstringGenerator(
                converter,
                self.module_name,
                self.source_code,
                quote=not issubclass(self.__class__, ast.NodeTransformer),
            )
            if converter
            else None
        )

    def report_missing_docstring(self) -> None:
        self.missing_docstrings += 1
        print(f'{".".join(self.stack)} is missing a docstring', file=sys.stderr)

    def handle_missing_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module:
        if self.docstring_generator:
            print('Hint:')
            print(self.docstring_generator.suggest_docstring(node))
            print()
        return node

    def process_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module:
        if (docstring := ast.get_docstring(node)) is None or docstring.strip() == '':
            self.report_missing_docstring()
            node = self.handle_missing_docstring(node)

        self.docstrings_inspected += 1
        return node

    def visit_node_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module:
        self.stack.append(getattr(node, 'name', self.module_name))

        node = self.process_docstring(node)

        self.generic_visit(node)
        self.stack.pop()
        return node

    def visit_Module(self, node: ast.Module) -> ast.Module:  # noqa: N802
        return self.visit_node_docstring(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:  # noqa: N802
        return self.visit_node_docstring(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:  # noqa: N802
        return self.visit_node_docstring(node)

    def visit_AsyncFunctionDef(  # noqa: N802
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        return self.visit_node_docstring(node)

    def process_file(self) -> None:
        self.visit(self.tree)

        if not self.missing_docstrings:
            print(f'No missing docstrings found in {self.source_file}.')
