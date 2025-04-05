from __future__ import annotations

import ast
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


class DocstringGenerator:
    def __init__(
        self,
        converter: type[DocstringConverter],
        module_name: str,
        source_code: str,
        quote: bool,
    ) -> None:
        self.converter = converter(quote=quote)
        self.module_name = module_name
        self.source_code = source_code

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

    def suggest_docstring(
        self,
        node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module,
        indent: int = 0,
    ) -> str:
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            return self.converter.to_function_docstring(
                Function(self.extract_arguments(node), self.extract_returns(node)),
                indent=indent,
            )

        if isinstance(node, ast.Module):
            return self.converter.to_module_docstring(self.module_name)

        return self.converter.to_class_docstring(node.name, indent=indent)
