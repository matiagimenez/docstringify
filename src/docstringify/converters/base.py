"""Base docstring converter."""

from __future__ import annotations

import ast
import textwrap
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..exceptions import InvalidDocstringError

if TYPE_CHECKING:
    from ..components import Parameter
    from ..nodes.base import DocstringNode


class DocstringConverter(ABC):
    def __init__(
        self,
        parameters_section_template: str,
        returns_section_template: str,
        quote: bool,
    ) -> None:
        self.parameters_section_template = parameters_section_template
        self.returns_section_template = returns_section_template
        self._quote = quote

    @abstractmethod
    def to_class_docstring(self, docstring_node: DocstringNode, indent: int) -> str:
        pass

    @abstractmethod
    def to_function_docstring(self, docstring_node: DocstringNode, indent: int) -> str:
        pass

    @abstractmethod
    def to_module_docstring(self, docstring_node: DocstringNode) -> str:
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

    def quote_docstring(self, docstring: str | list[str], indent: int) -> str:
        quote = '"""' if self._quote else ''
        prefix = sep = ''
        if isinstance(docstring, str):
            docstring = [quote, docstring, quote]
        elif isinstance(docstring, list):
            if len(docstring) > 1:
                prefix = ' ' * indent if indent else ''
                sep = '\n'
            docstring = [quote, *docstring, f'{prefix}{quote}']
        else:
            raise InvalidDocstringError(type(docstring).__name__)

        return textwrap.indent(sep.join(docstring), prefix)

    def suggest_docstring(
        self,
        docstring_node: DocstringNode,
        indent: int = 0,
    ) -> str | None:
        if isinstance(docstring_node.ast_node, ast.AsyncFunctionDef | ast.FunctionDef):
            return (
                self.to_function_docstring(docstring_node, indent=indent)
                if docstring_node.docstring_required
                else None
            )

        if isinstance(docstring_node.ast_node, ast.Module):
            return self.to_module_docstring(docstring_node)

        return self.to_class_docstring(docstring_node, indent=indent)
