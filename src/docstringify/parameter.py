"""Parameter representation."""

from collections import namedtuple
from typing import Final

NO_DEFAULT: Final = object()

Parameter = namedtuple('Parameter', ['name', 'type_', 'category', 'default'])
