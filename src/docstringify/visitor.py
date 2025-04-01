import ast
import itertools
from pathlib import Path


class DocstringVisitor(ast.NodeVisitor):
    def __init__(self, filename: str) -> None:
        self.source_file = Path(filename)
        self.source_code = self.source_file.read_text()

    def _extract_default_values(self, default, is_keyword_only, no_default) -> str:
        # Need to do it this way on Python <3.12 because they don't support nested f-strings yet
        if (not is_keyword_only and default is not no_default) or (
            is_keyword_only and default
        ):
            value = (
                f'"{default.value}"'
                if isinstance(default.value, str)
                else default.value
            )
            return f', default {value}'
        return ''

    def extract_arguments(self, node):
        modifiers = {
            'posonlyargs': 'positional-only',
            'kwonlyargs': 'keyword-only',
        }
        params = []

        positional_arguments_count = len(node.args.posonlyargs) + len(node.args.args)
        no_default = object()
        if (
            default_count := len(positional_defaults := node.args.defaults)
        ) < positional_arguments_count:
            positional_defaults = [no_default] * (
                positional_arguments_count - default_count
            ) + positional_defaults

        keyword_defaults = node.args.kw_defaults

        processed_positional_args = 0
        for arg_type, args in ast.iter_fields(node.args):
            if arg_type.endswith('defaults'):
                continue
            modifier = modifiers.get(arg_type)
            if arg_type in ['vararg', 'kwarg']:
                if args and arg_type == 'vararg':
                    params.append(f'*{args.arg}')
                if args and arg_type == 'kwarg':
                    params.append(f'**{args.arg}')
            else:
                is_keyword_only = arg_type.startswith('kw')
                params.extend(
                    [
                        (
                            f'{arg.arg} : {getattr(arg.annotation, "id", "__type__")}'
                            f'{f", {modifier}" if modifier else ""}'
                            f'{self._extract_default_values(default, is_keyword_only, no_default)}'
                            # f'{f", default {f'"{default.value}"' if isinstance(default.value, str) else default.value}" if (not is_keyword_only and default is not no_default) or (is_keyword_only and default) else ""}'
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
        if params and params[0].startswith(('self', 'cls')):
            return params[1:]
        return params

    def extract_returns(self, node):
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

    def suggest_docstring(self, node) -> str:
        docstring = ['"""', '__description__']

        if parameters := self.extract_arguments(node):
            docstring.extend(
                [
                    '',
                    'Parameters',
                    '----------',
                    *[
                        line
                        for couplet in zip(
                            parameters, itertools.repeat('    __description__')
                        )
                        for line in couplet
                    ],
                ]
            )

        if returns := self.extract_returns(node):
            docstring.extend(['', 'Returns', '-------', returns, '    __description__'])

        return '\n'.join([*docstring, '"""'])

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        if not ast.get_docstring(node):
            print(f'Function {node.name}() is missing a docstring')
            print('Hint:')
            print(self.suggest_docstring(node))
            print()

        self.generic_visit(node)

    def process_file(self) -> None:
        self.visit(ast.parse(self.source_code))


if __name__ == '__main__':
    visitor = DocstringVisitor('hello_world.py')
    visitor.process_file()
