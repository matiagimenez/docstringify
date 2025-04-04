from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from .components import (
    NO_DEFAULT,
    PARAMETER_TYPE_PLACEHOLDER,
    RETURN_TYPE_PLACEHOLDER,
    Function,
    Parameter,
)

if TYPE_CHECKING:
    from .converters import DocstringConverter


class DocstringVisitor(ast.NodeVisitor):
    def __init__(
        self, filename: str, converter: DocstringConverter | None = None
    ) -> None:
        self.source_file: Path = Path(filename)
        self.source_code: str = self.source_file.read_text()

        self.docstrings_inspected: int = 0
        self.missing_docstrings: int = 0

        self.module_name: str = self.source_file.stem
        self.stack: list[str] = []

        self.provide_hints: bool = converter is not None
        if self.provide_hints:
            self.converter: DocstringVisitor = converter  # TODO: consider whether this should be instantiated here instead of outside

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
                            type_=getattr(
                                args.annotation, 'id', PARAMETER_TYPE_PLACEHOLDER
                            ),
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
                            type_=getattr(
                                arg.annotation, 'id', PARAMETER_TYPE_PLACEHOLDER
                            ),
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
            return RETURN_TYPE_PLACEHOLDER
        return return_node

    def report_missing_docstring(self) -> None:
        self.missing_docstrings += 1
        print(f'{".".join(self.stack)} is missing a docstring', file=sys.stderr)

    def suggest_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> str:
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            return self.converter.to_function_docstring(
                Function(self.extract_arguments(node), self.extract_returns(node))
            )

        if isinstance(node, ast.Module):
            return self.converter.to_module_docstring(self.module_name)

        # TODO: with the stack, I should be able to let __init__() not have a docstring
        # and suggest those parameters as the docstring for the class
        # (may need to keep the class node in another stack)
        return self.converter.to_class_docstring(node.name)

    def process_docstring(
        self, node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
    ) -> None:
        if not ast.get_docstring(node):
            self.report_missing_docstring()
            if self.provide_hints:
                print('Hint:')
                print(self.suggest_docstring(node))
                print()

        self.docstrings_inspected += 1

    def visit(self, node: ast.AST) -> None:
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            self.stack.append(
                self.module_name if isinstance(node, ast.Module) else node.name
            )

            self.process_docstring(node)

            self.generic_visit(node)
            _ = self.stack.pop()

    def process_file(self) -> None:
        self.visit(ast.parse(self.source_code))
