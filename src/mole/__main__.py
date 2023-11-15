# -*- coding: utf-8 -*-
import os
import sys

import typer


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    if os.getenv("VIRTUAL_ENV") and sys.argv[0].endswith("mole"):
        typer.echo(
            "🐭 Error: detected poetry environment AND pipx entrypoint, this will surely cause PYTHONPATH conflicts, aborting"
        )
        sys.exit(1)
    from .cli import app

    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
