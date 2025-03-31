import ast
import itertools
from pathlib import Path


class DocstringTransformer(ast.NodeTransformer):

    def __init__(self, filename):
        self.source_file = Path(filename)
        self.source_code = self.source_file.read_text()

    def save(self, new_ast, *, overwrite=False):
        output = self.source_file if overwrite else self.source_file.parent / ('edited_' + self.source_file.name)
        edited_code = ast.unparse(new_ast)
        output.write_text(edited_code)
        print(f'Docstring templates written to {output}')
    
    def extract_arguments(self, node):
        modifiers = {
            'posonlyargs': 'positional-only',
            'kwonlyargs': 'keyword-only',
        }
        params = []

        positional_arguments_count = len(node.args.posonlyargs) + len(node.args.args)
        no_default = object()
        if (default_count := len(positional_defaults := node.args.defaults)) < positional_arguments_count:
            positional_defaults = [no_default] * (positional_arguments_count - default_count) + positional_defaults

        keyword_defaults = node.args.kw_defaults

        processed_positional_args = 0
        for arg_type, args in ast.iter_fields(node.args):
            if arg_type.endswith('defaults'):
                continue
            modifier = modifiers.get(arg_type)
            if arg_type in ["vararg", "kwarg"]:
                if args and arg_type == "vararg":
                    params.append(f"*{args.arg}")
                if args and arg_type == "kwarg":
                    params.append(f"**{args.arg}")
            else:
                is_keyword_only = arg_type.startswith('kw')
                params.extend(
                    [
                        (
                            f'{arg.arg} : {getattr(arg.annotation, "id", "__type__")}'
                            f'{f", {modifier}" if modifier else ""}'
                            f'{f", default {f'"{default.value}"' if isinstance(default.value, str) else default.value}" if (not is_keyword_only and default is not no_default) or (is_keyword_only and default) else ""}'
                        )
                        for arg, default in zip(
                            args,
                            keyword_defaults if is_keyword_only else positional_defaults[processed_positional_args:]
                        )
                    ]
                )
                if not is_keyword_only:
                    processed_positional_args += len(args)
                    
        params = tuple(params)
        if params and params[0].startswith(("self", "cls")):
            return params[1:]
        return params

    def extract_returns(self, node):
        if return_node := node.returns:
            if isinstance(return_node, ast.Constant):
                return return_node.value
            elif isinstance(return_node, ast.Name):
                return return_node.id
            return ast.get_source_segment(self.source_code, return_node)
        elif return_nodes := [body_node for body_node in node.body if isinstance(body_node, ast.Return)]:
            if any(
                not isinstance(return_value := body_return_node.value, ast.Constant)
                or return_value.value
                for body_return_node in return_nodes
            ):
                return '__return_type__'
        return return_node
    
    def suggest_docstring(self, node, col_offset):
        offset = ' ' * col_offset
        docstring = ['', '__description__']

        if parameters := self.extract_arguments(node):
            docstring.extend(
                [
                    '',
                    'Parameters',
                    '----------',
                    *[
                        line
                        for couplet in zip(parameters, itertools.repeat('    __description__'))
                        for line in couplet
                    ],
                ]
            )

        if returns := self.extract_returns(node):
            docstring.extend(['', 'Returns', '-------', returns, '    __description__'])

        return '\n'.join(f'{offset}{line}' for line in docstring + [''])

    def visit_FunctionDef(self, node):
        if not ast.get_docstring(node):
            print(f'Function {node.name}() is missing a docstring')
            docstring = ast.Expr(ast.Constant(self.suggest_docstring(node, node.col_offset + 4)))
            node.body.insert(0, docstring)
            return ast.fix_missing_locations(node)

    def process_file(self, *, overwrite=False):
        root = ast.parse(self.source_code)
        new_ast = self.visit(root)
        self.save(new_ast, overwrite=overwrite)

# transformer = DocstringTransformer('hello_world.py')
# transformer.process_file()
