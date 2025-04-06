from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from .visitor import DocstringVisitor

if TYPE_CHECKING:
    from .converters import DocstringConverter


class DocstringTransformer(ast.NodeTransformer, DocstringVisitor):
    def __init__(
        self, filename: str, converter: DocstringConverter, overwrite: bool = False
    ) -> None:
        super().__init__(filename, converter)
        self.overwrite = overwrite

    def save(self) -> None:
        if self.missing_docstrings:
            output = (
                self.source_file
                if self.overwrite
                else self.source_file.parent
                / (
                    self.source_file.stem
                    + '_docstringify'
                    + ''.join(self.source_file.suffixes)
                )
            )
            edited_code = ast.unparse(self.tree)
            output.write_text(edited_code)
            print(f'Docstring templates written to {output}')
        else:
            print(
                f'No missing docstrings found in {self.source_file}; no changes made.'
            )

    def handle_missing_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module:
        suggested_docstring = self.docstring_generator.suggest_docstring(
            node, indent=0 if isinstance(node, ast.Module) else node.col_offset + 4
        )
        docstring_node = ast.Expr(ast.Constant(suggested_docstring))

        if (
            current_docstring := ast.get_docstring(node)
        ) is not None and current_docstring.strip() == '':
            # If the docstring is empty, we replace it with the suggested docstring
            node.body[0] = docstring_node
        else:
            # If the docstring is missing, we insert the suggested docstring
            node.body.insert(0, docstring_node)
        return ast.fix_missing_locations(node)

    def process_file(self) -> ast.Module:
        self.tree = self.visit(self.tree)
        self.save()
        return self.tree
