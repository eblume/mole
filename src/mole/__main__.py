# -*- coding: utf-8 -*-
import logging
from pathlib import Path
import time

import typer

from mole.session import Session

from .motion import MotionRemote, MotionRemoteConfig

app = typer.Typer()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


@app.command()
def whack(config: Path):
    assert config.is_file()
    key = config.read_text().strip()
    assert len(key) == 44

    remote = MotionRemote.from_config(MotionRemoteConfig(key))
    session = Session(remote)
    session.resolve_actions(session.determine_actions())


@app.command()
def watch(config: Path):
    assert config.is_file()
    key = config.read_text().strip()
    assert len(key) == 44

    remote = MotionRemote.from_config(MotionRemoteConfig(key))
    session = Session(remote)
    while True:
        logging.debug("Main Loop")
        session.resolve_actions(session.determine_actions())
        time.sleep(20)


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
