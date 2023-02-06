# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import typer

from mole.session import Session

from .motion import MotionRemote, MotionRemoteConfig

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


def cli(config: Path):
    assert config.is_file()
    key = config.read_text().strip()
    assert len(key) == 44

    remote = MotionRemote.from_config(MotionRemoteConfig(key))
    session = Session(remote)
    session.resolve_actions(session.determine_actions())


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    typer.run(cli)


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
