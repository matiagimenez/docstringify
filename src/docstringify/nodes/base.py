from __future__ import annotations

import ast
from functools import partial
from typing import Callable, overload


class DocstringNode:
    @overload
    def __init__(
        self,
        node: ast.Module,
        module_name: str,
        source_code: str,
        parent: None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        module_name: str,
        source_code: str,
        parent: DocstringNode,
    ) -> None: ...

    def __init__(
        self,
        node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        module_name: str,
        source_code: str,
        parent: DocstringNode | None = None,
    ) -> None:
        self.module_name: str = module_name
        self.parent: DocstringNode | None = parent
        self._docstring_required: bool = True

        self.ast_node: (
            ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ) = node
        self.name: str = getattr(node, 'name', self.module_name)

        docstring = ast.get_docstring(node)
        self.docstring = docstring if docstring is None else docstring.strip()

        self.get_source_segment: Callable[[ast.AST], str] = partial(
            ast.get_source_segment, source_code
        )

    @property
    def fully_qualified_name(self) -> str:
        return (
            f'{self.parent.fully_qualified_name}.{self.name}'
            if self.parent
            else self.name
        )

    @property
    def docstring_required(self) -> bool:
        if self._has_decorator('overload'):
            return False
        return self._docstring_required

    @docstring_required.setter
    def docstring_required(self, value: bool) -> None:
        self._docstring_required = value

    def _has_decorator(self, decorator_name: str) -> bool:
        if not hasattr(self.ast_node, 'decorator_list'):
            return False

        return any(
            (isinstance(decorator, ast.Name) and decorator.id == decorator_name)
            or (
                isinstance(decorator, ast.Attribute)
                and decorator.attr == decorator_name
            )
            for decorator in self.ast_node.decorator_list
        )
