# docstringify
Flag missing docstrings and, optionally, generate them from signatures and type annotations.

## Usage

### Pre-commit hook

Add the following to your `.pre-commit-config.yaml` file to block commits with missing docstrings:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: 0.1.0
  hooks:
    - id: docstringify
```

By default, all docstrings are required. If you want to be more lenient, you can set the threshold, which is the percentage of docstrings that must be present:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: 0.1.0
  hooks:
    - id: docstringify
      args: [--threshold=0.75]
```

If you would like to see suggested docstring templates (inferred from type annotations for functions and methods), provide the `--suggest-changes` argument. By default, these will be [numpydoc-style docstrings](https://numpydoc.readthedocs.io/en/latest/format.html#); support for Google-style docstrings will come in a future release:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: 0.1.0
  hooks:
    - id: docstringify
      args: [--suggest-changes]
```

Be sure to check out the [pre-commit documentation](https://pre-commit.com/#pre-commit-configyaml---hooks) for additional configuration options.

### Command line

First, install the `docstringify` package from PyPI:

```shell
$ python -m pip install docstringify
```

Then, use the `docstringify` entry point on the file(s) of your choice:

```shell
$ docstringify /path/to/file [/path/to/another/file]
```

Run `docstringify --help` for more information.

### Python

First, install the `docstringify` package from PyPI:

```shell
$ python -m pip install docstringify
```

Then, use the `DocstringVisitor()` class on individual files to see spots where docstrings are missing:

```pycon
>>> from docstringify.visitor import DocstringVisitor
>>> visitor = DocstringVisitor('test.py')
>>> visitor.process_file()
test is missing a docstring
test.say_hello is missing a docstring
```

If you would like to see suggested docstring templates (inferred from type annotations for functions and methods), provide a converter:

```pycon
>>> from docstringify.converters.numpydoc import NumpydocDocstringConverter
>>> from docstringify.visitor import DocstringVisitor
>>> visitor = DocstringVisitor('test.py', converter=NumpydocDocstringConverter())
>>> visitor.process_file()
test is missing a docstring
Hint:
"""__description__"""

test.say_hello is missing a docstring
Hint:
"""
__description__

Parameters
----------
name : str, default="World"
    __description__
"""

```
