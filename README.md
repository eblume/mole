Mole
=======================
Copyright 2024 Erich Blume <blume.erich@gmail.com>
Provided under the MIT License. See LICENSE for more information.

Mole is a Python Typer CLI, a program which helps my personal automation.

For the most part, this repository is only intended to be directly helpful to myself, but sometimes I build things with
mole that wind up being useful to other people.

**mole changes rapidly with no warning and is not (yet) a candidate for stable deployment.** Use at your own risk.


How to Install
--------------

First, clone the repository with . Then use [pipx](https://pypa.github.io/pipx/) to install mole.

```bash
git clone http://github.com/eblume/mole
pipx install ./mole
```

You can later upgrade mole with `pipx upgrade mole` as per usual for pipx.

`mole` is not currently distributed in any packaging system. Please file an issue if you'd like to have one set up!
pip/PyPI, homebrew, asdf, apt, whatever people need, I'm happy to provide.

`mole` also currently does not provide binary distributions (wheels, containers, etc.) - similarly please file an issue
if you would like such a distribution format.


Requirements
------------
Most requirements are handled automatically via poetry/pip/pipx. There are some additional requirements, some of which
are optional.

* [op](https://developer.1password.com/docs/cli/get-started/) - handles credentialling. `op` is currently a hard
    requirement, including credentials with specific names needed throughout the codebase. This is of course impossible
    for anyone other than me to use, but luckily a future change to the `secrets.py` file should make this more
    portable.
* [nb-cli](https://github.com/xwmx/nb) - A program I use to save context streams and log activities and store metadata.
    I intend to eventually remove this dependency and instead use nb as one of an array of providers.
* [OpenAI](http://openai.com) - You will need to provide an OpenAI API key to use many of moles' features. I can't
    provide one for you.


How to Use
----------
Mole is self-documenting and provides a natural language interface via
[TyperAssistant](https://github.come/eblume/TyperAssistant). Use `mole ask "What can you do?"` and if mole can do it, it will be done! This is accomplished using the OpenAI [Assistants API](https://platform.openai.com/docs/assistants/overview) and incurs function-calling charges.

How to Develop
--------------

For MacOS, you'll want something like:

```bash
$ poetry install
$ poetry run pre-commit install
```

This will install a number of pre-commit hooks in your local clone of this
repository, which will ensure that you can't commit code that will break
this project. (You can bypass this with `git commit --no-verify`, but please be
careful.)

Please consult the [poetry](https://python-poetry.org/) docs for more information on how to develop in editable mode
using poetry.

A helper script, `bin/mole`, is provided which automatically activates the proper environment in a way that will
automatically detect and fail if something is crossing a pipx/poetry boundary.

How to Discuss
--------------

If you have design suggestions, questions, or bug reports - please file an
Issue on this github project.

How to Contribute
-----------------

Please see "How to Develop", and then submit a PR! It's fine to submit partial
PRs and/or pseudocode. I don't bite.
