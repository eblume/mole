Funicular
=========

Funicular is an IN DEVELOPMENT project that provides a convenient api and query
DSL for searching python code. It is tightly linked with the `ast` package:
you can approximately think of it as an opinionated frontend to `ast`, that makes
it easy to perform assertions on python code.


How to Install
--------------

Funicular will eventually be released on PyPI, but until then, you can use it
in your projects by installing directly from this github repository:

```bash
$ python -m pip install git+https://github.com/eblume/funicular.git
```

You can then import `funicular` as you would any other python package. You may
also wish to investigate a PEP-517 compliant build tool such as `poetry` or
`pipenv` for your project.

How to Use / Utilize
--------------------

While Funicular is in development, the code itself is the best source of
documentation. You may find the tests to be helpful in learning what Funicular
can do.

How to Test
-----------

Funicular uses `pyproject.toml` to track all root and development dependencies,
including the entire build chain. `nox` is used to handle creating and isolating
the build/test environment to ensure clean, reproducable builds. `poetry` is
used by nox to handle installing the project and all dependencies.

Therefore, there are two ways to go from a fresh `python` installation to building
and testing `funicular`:

1. Use `poetry` to run nox (and handle installing nox and all other deps)::

   ```bash
   # Install poetry on a POSIX system (re-installation is upgrade-or-noop)
   # (a Windows installer exists as well, see python-poetry.org)
   $ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

   $ poetry run nox
   ```

   This will end up installing the requirements twice, though - once for your
   root project (in a virtual env), and once inside of the `nox` test. This is
   fine - in fact, this is how I handle it, because the root project also
   includes packages that help development, e.g. `isort` and `flake8`.

   (NB: You can also just `pip install poetry`, but this has
   [known issues](https://python-poetry.org/docs/#alternative-installation-methods-not-recommended).)

2. Use `nox` directly::

   ```bash
   $ pip install nox
   $ nox
   ```

   This is obviously much simpler, but then you don't get direct access to
   `poetry`, `flake8`, `isort`, etc. in your development environment.


Of course, you can also simply run `pytest` manually. You might find that doing
so inside of `poetry shell` is a useful idiom, especially if you decide to
develop for `funicular`.

How to Develop
--------------

Before doing any development on Funicular, please install `poetry` as per
option 1 of the "How to Test" section, above. **Then, please run the following**:

```bash
$ poetry run pre-commit install
```

This will install a number of pre-commit hooks in your local clone of this
repository, which will ensure that you can't commit code that will break
Funicular. (You can bypass this with `git commit --no-verify`, but please be
careful.)

I will attempt to increase the documentation around Funicular's API, but for
now you are probably best off reading the test code for comprehension and the
source for "the API".

How to Discuss
--------------

If you have design suggestions, questions, or bug reports - please file an
Issue on this github project. You can also email me at blume.erich@gmail.com,
but to be honest, I'm not the best at checking my email. Issues are more likely
to be seen.

How to Contribute
-----------------

Please see "How to Develop", and then submit a PR! It's fine to submit partial
PRs and/or pseudocode. Once the simulator is working, we will probably have
some further guidelines for contributing. But that's a ways off yet.
