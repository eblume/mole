# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import click

from .engine import Engine

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


@click.argument("script", type=click.Path(exists=True, path_type=Path))
@click.command()
def cli(script: Path):
    engine = Engine(script)
    engine.start()
