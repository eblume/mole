# -*- coding: utf-8 -*-
"""Storage layer for task and task-related data.

The intention is that this layer should allow for different backends, as well as a source-agnostic ingestion layer via
the StoreUpdater class.
"""

from __future__ import annotations

import abc
import asyncio
from dataclasses import dataclass, field
import logging
from typing import Iterable, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .engine import Engine
    from .models import Task


class Store(abc.ABC):
    @abc.abstractmethod
    def __init__(self, engine: Engine):
        raise NotImplementedError

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    @abc.abstractmethod
    async def update(self, update: StoreUpdater) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def __contains__(self, item: Task) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def add_task(self, task: Task) -> None:
        raise NotImplementedError


@dataclass
class DumbStore(Store):
    """An extremely basic example of a Store that uses python primitives.

    Not intended for serious use. See SqliteStore for a straightforward replacement (if it's been added yet).
    """

    # TODO ^ make SqliteStore

    engine: Engine
    write_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    tasks: List[Task] = field(default_factory=list)

    async def update(self, update: StoreUpdater) -> None:
        async with self.write_lock:
            if update.should_clear():
                self.log.debug("Clearing task cache")
                self.tasks = []

            for task in update.new_tasks():
                self.tasks.append(task)
                self.engine.events.NEW_TASK.publish(task)

    def __contains__(self, task: Task) -> bool:
        return task in self.tasks

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)


class StoreUpdater(abc.ABC):
    @abc.abstractmethod
    def new_tasks(self) -> Iterable[Task]:
        raise NotImplementedError

    @abc.abstractmethod
    def should_clear(self) -> bool:
        raise NotImplementedError
