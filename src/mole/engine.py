# -*- coding: utf-8 -*-
import asyncio
import logging
from pathlib import Path
from signal import SIGINT, SIGTERM

from .config import Config
from .remote import SyncClient


class EngineAlreadyRunning(Exception):
    def __init__(self, *args, **kwargs):
        # TODO: Find a better way to word this to explain that engines are kinda singletons.
        super().__init__(self, "The engine is already running.", *args, **kwargs)


class SyncError(Exception):
    pass


class Engine:
    # Instance variables

    config: Config

    # Sync Methods

    def __init__(self, config_file: Path) -> None:
        self.config = Config.load_via_module(config_file)

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def start(self) -> None:
        loop = asyncio.get_event_loop()
        try:
            self.log.debug("Main event loop starting")
            loop.run_until_complete(self.run())
            loop.run_forever()
            self.log.debug("Main event loop complete")
        finally:
            self.log.debug("Main event loop closing")
            loop.close()
            self.log.debug("Main event loop closed")
            loop.stop()

        self.log.debug("Engine.start() returned")

    # Async Methods

    async def run(self) -> None:
        # This function should so whatever setup is needed to create independent isolated subprocesses,
        # and then call their main functions in a `gather` call at the end.

        sync_client = self.config.make_client(self)
        # printer = ItemEventPrinter(self)

        asyncio.gather(
            # self.printer.run(),
            sync_client.run(),
        )
