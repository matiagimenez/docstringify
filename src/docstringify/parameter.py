"""Parameter representation."""

from collections import namedtuple

NO_DEFAULT = object()

Parameter = namedtuple('Parameter', ['name', 'type_', 'category', 'default'])
