# -*- coding: utf-8 -*-
import typer

from .cli import cli

if __name__ == "__main__":
    # It always SHOULD be, but let's check anyway.
    typer.run(cli)
