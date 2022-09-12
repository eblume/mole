# -*- coding: utf-8 -*-
import asyncio
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .components import ItemEventPrinter
from .config import Config
from .events import Events
from .store import Store


class EngineAlreadyRunning(Exception):
    def __init__(self, *args, **kwargs):
        # TODO: Find a better way to word this to explain that engines are kinda singletons.
        super().__init__(self, "The engine is already running.", *args, **kwargs)


class SyncError(Exception):
    pass


@dataclass
class Engine:
    # Instance variables

    config: Config
    store: Store = field(init=False)
    events: Events = field(init=False)

    # Sync Methods

    def __post_init__(self):
        self.store = self.config.make_store(self)
        self.events = Events(self)

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    async def run(self) -> None:
        """'run' the Engine, which uses the Config to handle setup for the relevant components.

        This coroutine will not complete under normal circumstances. It is expected that the caller will cancel this
        coroutine when it is time for execution to end. (A user ctrl+c is the most likely path to exit.)
        """
        # This function should so whatever setup is needed to create independent isolated subprocesses,
        # and then call their main functions in a `gather` call at the end.

        sync_client = self.config.make_client(self)
        printer = ItemEventPrinter(self)

        await asyncio.gather(
            printer.run(),
            sync_client.run(),
        )
