"""Base docstring converter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..components import Function, Parameter


class DocstringConverter(ABC):
    def __init__(
        self, parameters_section_template: str, returns_section_template: str
    ) -> None:
        self.parameters_section_template = parameters_section_template
        self.returns_section_template = returns_section_template

    @abstractmethod
    def to_class_docstring(self, class_name: str) -> str:
        pass

    @abstractmethod
    def to_function_docstring(self, function: Function) -> str:
        pass

    @abstractmethod
    def to_module_docstring(self, module_name: str) -> str:
        pass

    @abstractmethod
    def format_parameter(self, parameter: Parameter) -> str:
        pass

    def parameters_section(self, parameters: tuple[Parameter, ...]) -> str:
        if parameters:
            return self.parameters_section_template.format(
                parameters='\n'.join(
                    self.format_parameter(parameter) for parameter in parameters
                )
            )
        return ''

    @abstractmethod
    def format_return(self, return_type: str | None) -> str:
        pass

    def returns_section(self, return_type: str | None) -> str:
        if return_text := self.format_return(return_type):
            return self.returns_section_template.format(returns=return_text)
        return ''
