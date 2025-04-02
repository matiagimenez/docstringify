"""Numpydoc-style docstring converter."""

from __future__ import annotations

from ..parameter import NO_DEFAULT, Parameter
from .base import DocstringConverter


class NumpydocDocstringConverter(DocstringConverter):
    def __init__(self) -> None:
        super().__init__(
            parameters_section_template='Parameters\n----------\n{parameters}',
            returns_section_template='Returns\n-------\n{returns}',
        )

    def to_docstring(
        self, parameters: tuple[Parameter, ...], return_type: str | None
    ) -> str:
        # TODO: the visitor needs the triple quotes but the transformer does not
        docstring = ['"""', '__description__']

        if parameters_section := self.parameters_section(parameters):
            docstring.extend(['', parameters_section])

        if returns_section := self.returns_section(return_type):
            docstring.extend(['', returns_section])

        sep = '' if len(docstring) == 2 else '\n'

        return sep.join([*docstring, '"""'])

    def format_parameter(self, parameter: Parameter) -> str:
        return (
            f'{parameter.name} : {parameter.type_}'
            f'{f", {parameter.category}" if parameter.category else ""}'
            f'{f", default={parameter.default}" if parameter.default != NO_DEFAULT else ""}'
            '\n    __description__'
        )

    def format_return(self, return_type: str | None) -> str:
        if return_type:
            return f'{return_type}\n    __description__'
        return ''
