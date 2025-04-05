"""Google-style docstring converter."""

from __future__ import annotations

from ..components import DESCRIPTION_PLACEHOLDER, NO_DEFAULT, Function, Parameter
from .base import DocstringConverter


class GoogleDocstringConverter(DocstringConverter):
    def __init__(self, quote: bool) -> None:
        super().__init__(
            parameters_section_template='Args:\n{parameters}',
            returns_section_template='Returns:\n    {returns}',
            quote=quote,
        )

    def to_function_docstring(self, function: Function, indent: int) -> str:
        docstring = [DESCRIPTION_PLACEHOLDER]

        if parameters_section := self.parameters_section(function.parameters):
            docstring.extend(['', parameters_section])

        if returns_section := self.returns_section(function.return_type):
            docstring.extend(['', returns_section])

        return self.quote_docstring(docstring, indent=indent)

    def format_parameter(self, parameter: Parameter) -> str:
        category = f'{f", {parameter.category}" if parameter.category else ""}'
        return (
            f'    {parameter.name} ({parameter.type_}{category}): {DESCRIPTION_PLACEHOLDER}'
            f'{f" Defaults to {parameter.default}." if parameter.default != NO_DEFAULT else ""}'
        )

    def format_return(self, return_type: str | None) -> str:
        if return_type:
            return f'{return_type}: {DESCRIPTION_PLACEHOLDER}'
        return ''

    def to_module_docstring(self, module_name: str) -> str:
        return self.quote_docstring(DESCRIPTION_PLACEHOLDER, indent=0)

    def to_class_docstring(self, class_name: str, indent: int) -> str:
        return self.quote_docstring(DESCRIPTION_PLACEHOLDER, indent=indent)
