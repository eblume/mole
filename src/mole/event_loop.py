# NOTE TO SELF: Try and relegate all `async` related code to this module.
# This will allow easier swapping in of other event loops (such as gevent or a static loop)
# without having to refactor out of asyncio.

import asyncio
from dataclasses import dataclass
import logging

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EventLoop:
    # Sync methods

    def start(self) -> None:
        log.debug("Beginning asyncio event loop")
        asyncio.run(self.loop())

    # Async methods

    async def loop(self) -> None:
        log.info("Event loop started")
        await self.safe_shutdown()

    async def safe_shutdown(self) -> None:
        log.info("Event loop ending naturally. Goodbye!")
