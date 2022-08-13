# -*- coding: utf-8 -*-
import asyncio
import logging
from pathlib import Path
from typing import Optional

from .config import Config
from .todoist import TodoistAPI


class EngineAlreadyRunning(Exception):
    def __init__(self, *args, **kwargs):
        # TODO: Find a better way to word this to explain that engines are kinda singletons.
        super().__init__(self, "The engine is already running.", *args, **kwargs)


class SyncError(Exception):
    pass


class Engine:
    # Instance variables

    config: Config
    client: Optional[TodoistAPI] = None

    # Sync Methods

    def __init__(self, config_file: Path) -> None:
        self.config = Config.load_via_module(config_file)

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def start(self) -> None:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(asyncio.gather(self.main()))

    # Async Methods

    async def main(self) -> None:
        self.log.debug("Starting async tasks")
        client = await self.get_client()
        task = asyncio.create_task(client.start())
        # TODO do useful things here
        await asyncio.sleep(60)
        await client.stop()
        await task

    async def get_client(self) -> TodoistAPI:
        # Note: this is async so that in the future we can maybe use asyncio.Condition or some other
        # such construct to be smarter about the lifecycle of the client, and be sure that we aren't
        # running in to issues with asyncio + todoist. Hopefully, until then, this bodge will hold.
        if self.client is None:
            self.client = TodoistAPI.from_api_key(self.config.api_key)
            self.client.debug = self.config.debug
        return self.client
