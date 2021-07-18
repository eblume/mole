import asyncio
import datetime as dt
import logging
from typing import Optional

import todoist

from .config import Config


class EngineAlreadyRunning(Exception):
    def __init__(self, *args, **kwargs):
        # TODO: Find a better way to word this to explain that engines are kinda singletons.
        super().__init__(self, "The engine is already running.")


class Engine:
    # Instance variables

    config: Config
    client: Optional[todoist.TodoistAPI] = None
    whack_a_mole_item: Optional[todoist.models.Item] = None

    # Constants

    SYNC_INTERVAL = dt.timedelta(seconds=5)  # TODO tune down when live
    WHACKAMOLE_INTERVAL = dt.timedelta(seconds=5)  # TODO tune down when live

    # Sync Methods

    def __init__(self) -> None:
        # TODO - allow command line and env overrides, via click maybe?
        # TODO - add --config parameter to click, pass to load_via_env
        self.config = Config.load_via_env()

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def run_forever(self) -> None:
        asyncio.run(self.start())

    # Async Methods

    async def start(self) -> None:
        self.log.debug("Starting async tasks")
        # In the future, when multiple loops exist, use `await asyncio.gather(...)`
        await self.whack_a_mole_loop()
        self.log.debug("Exiting successfully after gathering scheduled tasks")

    async def whack_a_mole_loop(self) -> None:
        while True:  # TODO exit signal
            self.log.debug("whack_a_mole_loop")
            client = await self.get_client()
            await self.whack_a_mole(client)
            await asyncio.sleep(self.WHACKAMOLE_INTERVAL.total_seconds())

    async def whack_a_mole(self, client: todoist.TodoistAPI) -> None:
        self.log.debug("whack_a_mole")

        if self.whack_a_mole_item is None:
            item = client.items.add("Click me!")
            client.commit()
            self.whack_a_mole_item = item
        else:
            self.whack_a_mole_item.update()
            client.commit()

        if self.whack_a_mole_item['checked']:
            self.log.info("oh no, someone whacked the mole")
            item = client.items.add("Click me too!")
            client.commit()
            self.whack_a_mole_item = item

    async def get_client(self) -> todoist.TodoistAPI:
        # Note: this is async so that in the future we can maybe use asyncio.Condition or some other
        # such construct to be smarter about the lifecycle of the client, and be sure that we aren't
        # running in to issues with asyncio + todoist. Hopefully, until then, this bodge will hold.
        if self.client is None:
            self.client = todoist.TodoistAPI(self.config.api_key)
        return self.client
