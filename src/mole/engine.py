# -*- coding: utf-8 -*-
import asyncio
import datetime as dt
import logging
from pathlib import Path
from typing import Optional

import todoist

from .config import Config


class EngineAlreadyRunning(Exception):
    def __init__(self, *args, **kwargs):
        # TODO: Find a better way to word this to explain that engines are kinda singletons.
        super().__init__(self, "The engine is already running.", *args, **kwargs)


class SyncError(Exception):
    pass


class Engine:
    # Instance variables

    config: Config
    client: Optional[todoist.TodoistAPI] = None

    # Constants

    SYNC_INTERVAL = dt.timedelta(seconds=5)  # TODO tune down when live

    # Sync Methods

    def __init__(self, config_file: Path) -> None:
        self.config = Config.load_via_module(config_file)

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def run_forever(self) -> None:
        asyncio.run(self.start())

    # Async Methods

    async def start(self) -> None:
        self.log.debug("Starting async tasks")
        # In the future, when multiple loops exist, use `await asyncio.gather(...)`
        await self.api_test()
        self.log.debug("Exiting successfully after gathering scheduled tasks")

    async def get_client(self) -> todoist.TodoistAPI:
        # Note: this is async so that in the future we can maybe use asyncio.Condition or some other
        # such construct to be smarter about the lifecycle of the client, and be sure that we aren't
        # running in to issues with asyncio + todoist. Hopefully, until then, this bodge will hold.
        if self.client is None:
            self.client = todoist.TodoistAPI(self.config.api_key)
            await self.process_sync(self.client.sync())
        return self.client

    async def process_sync(self, sync_data):
        # TODO: actually do something with this sync_data to create a synchronous client, maybe?
        if "error" in sync_data:
            raise SyncError(sync_data)

    async def api_test(self):
        client = await self.get_client()
        client.sync()
        # TODO write api stuff here, delete this eventually, lol
