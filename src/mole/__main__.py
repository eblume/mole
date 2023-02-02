# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import typer

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


def cli(script: Path):
    print(script)


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    typer.run(cli)


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
