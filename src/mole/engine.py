import asyncio
import datetime as dt
import logging
from typing import Dict


class EngineAlreadyRunning(Exception):
    def __init__(self, *args, **kwargs):
        # TODO: Find a better way to word this to explain that engines are kinda singletons.
        super().__init__(self, "The engine is already running.")


class Engine:
    tasks: Dict[str, asyncio.Task] = {}  # This is a CLASS variable!

    SYNC_INTERVAL = dt.timedelta(milliseconds=1)  # TODO tune down when live

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def run_forever(self) -> None:
        if len(self.tasks) > 0:
            raise EngineAlreadyRunning()

        asyncio.run(self.start())

    async def start(self) -> None:
        self.tasks["sync_loop"] = asyncio.create_task(self.sync_loop())
        await self.tasks['sync_loop']

    async def sync_loop(self) -> None:
        self.log.debug("sync_loop")

        # Loop
        while True:
            await asyncio.sleep(self.SYNC_INTERVAL.total_seconds())
            self.log.debug("sync_loop woke")
