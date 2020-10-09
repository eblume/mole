# -*- coding: utf-8 -*-
import nox


@nox.session(python=["3.8"],)  # No plans for <3.8, file an issue if you are impacted!
def tests(session):
    session.install(".")
    session.run("poetry", "install", external=True)

    args = session.posargs or []  # add default args to pyproject.toml, not here

    session.run("python", "-m", "pytest", *args)
