import datetime as dt
import abc
import asyncio
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import Client
    from .engine import Engine


class ServiceRunningError(Exception):
    pass


class Service(abc.ABC):

    _engine: Engine

    def __init__(self, engine: Engine):
        self._engine = engine

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    async def start(self) -> None:
        self.log.info(f"Starting service: {self.__class__.__name__}.")
        await self.initialize(self._engine)

    # Abstract Methods

    @abc.abstractmethod
    async def initialize(self, engine: Engine) -> None:
        raise NotImplementedError("Base classes must implement this method")

    @property
    @abc.abstractmethod
    def engine(self) -> Engine:
        raise NotImplementedError("Base classes must implement this method")


class ClientSyncService(Service):

    _client: Optional[Client] = None
    _task: Optional[asyncio.Task] = None

    POLL_INTERVAL = dt.timedelta(seconds=30)

    @property
    def engine(self) -> Engine:
        return self._engine

    async def initialize(self, engine: Engine) -> None:
        if self._task is not None:
            raise ServiceRunningError(f"Service {self.__class__.__name__} already running")

        self._client = await self.engine.get_client()

        # Start service loop
        self._task = asyncio.create_task(self.loop())

    async def loop(self) -> None:
        await self._client.sync()
        await asyncio.sleep(self.POLL_INTERVAL.total_seconds())
