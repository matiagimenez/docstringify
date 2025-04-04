from __future__ import annotations

import argparse
import sys
from typing import Sequence

from . import __version__
from .converters.google import GoogleDocstringConverter
from .converters.numpydoc import NumpydocDocstringConverter
from .visitor import DocstringVisitor

PROG = __package__


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=PROG)
    parser.add_argument(
        'filenames',
        nargs='*',
        help='Filenames to process',
    )
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )

    parser.add_argument(
        '--suggest-changes',
        action='store_true',
        help='Whether to print out docstring templates for items missing docstrings',
    )
    parser.add_argument(
        '--style',
        choices=['google', 'numpydoc'],
        default='numpydoc',
        help='The style of docstring to use (only used when --suggest-changes is passed)',
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=1,
        help='The percentage of docstrings that must be present to pass',
    )
    args = parser.parse_args(argv)

    if args.style is None or not args.suggest_changes:
        converter = None
    elif args.style == 'google':
        converter = GoogleDocstringConverter()
    elif args.style == 'numpydoc':
        converter = NumpydocDocstringConverter()
    else:
        raise NotImplementedError(f'{args.style} is not a supported option')

    docstrings_processed = missing_docstrings = 0
    for file in args.filenames:
        visitor = DocstringVisitor(file, converter=converter)
        visitor.process_file()
        missing_docstrings += visitor.missing_docstrings
        docstrings_processed += visitor.docstrings_inspected

    if docstrings_processed and (
        missing_percentage := (missing_docstrings / docstrings_processed)
    ) > (1 - args.threshold):
        print(f'Missing {missing_percentage:.0%} of docstrings', file=sys.stderr)
        print(
            f'Your settings require {args.threshold:.0%} of docstrings to be present',
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
