# -*- coding: utf-8 -*-
import logging

import click

from .engine import Engine

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


@click.command()
def cli():
    click.echo("Let's play whack-a-mole")

    engine = Engine()
    engine.run_forever()
