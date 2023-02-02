# -*- coding: utf-8 -*-
import logging
from pathlib import Path

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


def cli(script: Path):
    print(script)
