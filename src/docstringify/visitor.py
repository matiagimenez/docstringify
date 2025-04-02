from __future__ import annotations

import ast
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from .converters.numpydoc import NumpydocDocstringConverter
from .parameter import NO_DEFAULT, Parameter

if TYPE_CHECKING:
    from .converters.base import DocstringConverter


class DocstringVisitor(ast.NodeVisitor):
    def __init__(
        self, filename: str, converter: DocstringConverter | None = None
    ) -> None:
        self.source_file = Path(filename)
        self.source_code = self.source_file.read_text()
        self.provide_hints = converter is not None
        if self.provide_hints:
            self.converter = converter  # TODO: consider whether this should be instantiated here instead of outside

    def _extract_default_values(
        self, default: ast.Constant | None | Literal[NO_DEFAULT], is_keyword_only: bool
    ) -> str | Literal[NO_DEFAULT]:
        if (not is_keyword_only and default is not NO_DEFAULT) or (
            is_keyword_only and default
        ):
            try:
                default_value = default.value
            except AttributeError:
                default_value = f'`{default.id}`'

            return (
                f'"{default_value}"'
                if isinstance(default_value, str) and not default_value.startswith('`')
                else default_value
            )
        return NO_DEFAULT

    def extract_arguments(
        self, node: ast.AsyncFunctionDef | ast.FunctionDef
    ) -> tuple[Parameter, ...]:
        modifiers = {
            'posonlyargs': 'positional-only',
            'kwonlyargs': 'keyword-only',
        }
        params = []

        positional_arguments_count = len(node.args.posonlyargs) + len(node.args.args)
        if (
            default_count := len(positional_defaults := node.args.defaults)
        ) < positional_arguments_count:
            positional_defaults = [NO_DEFAULT] * (
                positional_arguments_count - default_count
            ) + positional_defaults

        keyword_defaults = node.args.kw_defaults

        processed_positional_args = 0
        for arg_type, args in ast.iter_fields(node.args):
            if arg_type.endswith('defaults'):
                continue
            modifier = modifiers.get(arg_type)
            if arg_type in ['vararg', 'kwarg']:
                if args:
                    params.append(
                        Parameter(
                            name=f'*{args.arg}'
                            if arg_type == 'vararg'
                            else f'**{args.arg}',
                            type_=getattr(args.annotation, 'id', '__type__'),
                            category=modifier,
                            default=NO_DEFAULT,
                        )
                    )
            else:
                is_keyword_only = arg_type.startswith('kw')
                params.extend(
                    [
                        Parameter(
                            name=arg.arg,
                            type_=getattr(arg.annotation, 'id', '__type__'),
                            category=modifier,
                            default=self._extract_default_values(
                                default, is_keyword_only
                            ),
                        )
                        for arg, default in zip(
                            args,
                            keyword_defaults
                            if is_keyword_only
                            else positional_defaults[processed_positional_args:],
                        )
                    ]
                )
                if not is_keyword_only:
                    processed_positional_args += len(args)

        params = tuple(params)
        if (
            params
            and isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and params[0].name.startswith(('self', 'cls'))
        ):
            return params[1:]
        return params

    def extract_returns(
        self, node: ast.AsyncFunctionDef | ast.FunctionDef
    ) -> str | None:
        if return_node := node.returns:
            if isinstance(return_node, ast.Constant):
                return return_node.value
            if isinstance(return_node, ast.Name):
                return return_node.id
            return ast.get_source_segment(self.source_code, return_node)
        if (
            return_nodes := [
                body_node
                for body_node in node.body
                if isinstance(body_node, ast.Return)
            ]
        ) and any(
            not isinstance(return_value := body_return_node.value, ast.Constant)
            or return_value.value
            for body_return_node in return_nodes
        ):
            return '__return_type__'
        return return_node

    def suggest_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> str:
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            return self.converter.to_docstring(
                self.extract_arguments(node), self.extract_returns(node)
            )
        raise NotImplementedError(
            'Docstrings for classes and modules are not supported yet'
        )

    def process_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> None:
        if not ast.get_docstring(node):
            # TODO: print class.method() instead of just the method name
            # TODO: print module name with each
            print(f'Function {node.name}() is missing a docstring')
            if self.converter:
                print('Hint:')
                print(self.suggest_docstring(node))
                print()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.process_docstring(node)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self.process_docstring(node)
        self.generic_visit(node)

    def process_file(self) -> None:
        self.visit(ast.parse(self.source_code))


if __name__ == '__main__':
    visitor = DocstringVisitor(
        'test_file.py',
        converter=NumpydocDocstringConverter(),
    )
    visitor.process_file()
