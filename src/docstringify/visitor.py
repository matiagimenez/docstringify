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

        self.docstrings_inspected: int = 0
        self.missing_docstrings: int = 0

        self.module_name: str = self.source_file.stem
        self.stack: list[str] = []

        self.provide_hints: bool = converter is not None
        if self.provide_hints:
            self.docstring_generator = DocstringGenerator(
                converter,
                self.module_name,
                self.source_code,
                quote=not issubclass(self.__class__, ast.NodeTransformer),
            )

    def report_missing_docstring(self) -> None:
        self.missing_docstrings += 1
        print(f'{".".join(self.stack)} is missing a docstring', file=sys.stderr)

    def handle_missing_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module:
        if self.provide_hints:
            print('Hint:')
            print(self.docstring_generator.suggest_docstring(node))
            print()
        return node

    def process_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module:
        if not ast.get_docstring(node):
            self.report_missing_docstring()
            node = self.handle_missing_docstring(node)

        self.docstrings_inspected += 1
        return node

    def visit(self, node: ast.AST) -> ast.AST:
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            self.stack.append(
                self.module_name if isinstance(node, ast.Module) else node.name
            )

            node = self.process_docstring(node)

            self.generic_visit(node)
            _ = self.stack.pop()
        return node

    def process_file(self) -> ast.Module:
        root = self.visit(ast.parse(self.source_code))

        if not self.missing_docstrings:
            print(f'No missing docstrings found in {self.source_file}.')

        return root
