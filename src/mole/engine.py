import asyncio
import logging
from typing import Iterable

from .client import Client, DummyClient
from .services import Service, WhackAMole


class Engine:
    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def run(self) -> None:
        self.log.debug("Starting services")
        for service in self.services():
            asyncio.run(service.start())

    def services(self) -> Iterable[Service]:
        yield

    async def get_client(self) -> Client:
        # TODO real client. Async.
        return DummyClient()
