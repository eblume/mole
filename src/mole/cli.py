# -*- coding: utf-8 -*-
import asyncio
import logging
from pathlib import Path

from .config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


def cli(script: Path):
    config = Config.load_via_module(script)
    engine = config.make_engine()
    asyncio.run(engine.run())
