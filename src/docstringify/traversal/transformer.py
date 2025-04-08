from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from .visitor import DocstringVisitor

if TYPE_CHECKING:
    from ..converters import DocstringConverter
    from ..nodes.base import DocstringNode


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

    def handle_missing_docstring(self, docstring_node: DocstringNode) -> DocstringNode:
        suggested_docstring = self.docstring_converter.suggest_docstring(
            docstring_node,
            indent=0
            if isinstance(docstring_node.node, ast.Module)
            else docstring_node.node.col_offset + 4,
        )
        docstring_ast_node = ast.Expr(ast.Constant(suggested_docstring))

        if (
            docstring_node.docstring is not None
            and docstring_node.docstring.strip() == ''
        ):
            # If the docstring is empty, we replace it with the suggested docstring
            docstring_node.node.body[0] = docstring_ast_node
        else:
            # If the docstring is missing, we insert the suggested docstring
            docstring_node.node.body.insert(0, docstring_ast_node)

        docstring_node.node = ast.fix_missing_locations(docstring_node.node)

        return docstring_node

    def process_file(self) -> None:
        super().process_file()
        self.save()
