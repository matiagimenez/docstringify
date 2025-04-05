"""Docstringify exceptions."""


class InvalidDocstringError(ValueError):
    def __init__(self, docstring_class: str) -> None:
        super().__init__(f'Expected str or list[str] docstring, got {docstring_class}')
