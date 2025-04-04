"""Google-style docstring converter."""

from __future__ import annotations

from ..components import DESCRIPTION_PLACEHOLDER, NO_DEFAULT, Function, Parameter
from .base import DocstringConverter


class GoogleDocstringConverter(DocstringConverter):
    def __init__(self) -> None:
        super().__init__(
            parameters_section_template='Args:\n{parameters}',
            returns_section_template='Returns:\n    {returns}',
        )

    def to_function_docstring(self, function: Function) -> str:
        # TODO: the visitor needs the triple quotes but the transformer does not
        docstring = [f'"""{DESCRIPTION_PLACEHOLDER}']

        if parameters_section := self.parameters_section(function.parameters):
            docstring.extend(['', parameters_section])

        if returns_section := self.returns_section(function.return_type):
            docstring.extend(['', returns_section])

        sep = '' if len(docstring) == 1 else '\n'

        return sep.join([*docstring, '"""'])

    def format_parameter(self, parameter: Parameter) -> str:
        category = f'{f", {parameter.category}" if parameter.category else ""}'
        return (
            f'    {parameter.name} ({parameter.type_}{category}): {DESCRIPTION_PLACEHOLDER} '
            f'{f" Defaults to {parameter.default}." if parameter.default != NO_DEFAULT else ""}'
        )

    def format_return(self, return_type: str | None) -> str:
        if return_type:
            return f'{return_type}: {DESCRIPTION_PLACEHOLDER}'
        return ''

    def to_module_docstring(self, module_name: str) -> str:
        return f'"""{DESCRIPTION_PLACEHOLDER}"""'

    def to_class_docstring(self, class_name: str) -> str:
        return f'"""{DESCRIPTION_PLACEHOLDER}"""'
