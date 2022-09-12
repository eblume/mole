# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
from typing import Generic, List, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from .engine import Engine
    from .models import Task


@dataclass
class Events:
    engine: Engine
    NEW_TASK: Event[Task] = field(init=False)

    def __post_init__(self):
        self.NEW_TASK = Event("new_task")


MessageT = TypeVar("MessageT")


@dataclass
class Event(Generic[MessageT]):
    name: str
    subscribers: List[Subscription[MessageT]] = field(default_factory=list)

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    def subscribe(self) -> Subscription[MessageT]:
        # Note that only when we __enter__ do we record the subscriber
        return Subscription(self)

    def publish(self, message: MessageT):
        self.log.debug("Publishing message: %s", str(message))
        for subscriber in self.subscribers:
            subscriber.queue.put_nowait(message)


@dataclass
class Subscription(Generic[MessageT]):
    event: Event
    queue: asyncio.Queue[MessageT] = field(default_factory=asyncio.Queue)

    def __enter__(self) -> asyncio.Queue[MessageT]:
        self.event.subscribers.append(self)
        return self.queue

    def __exit__(self, type, value, traceback):
        # TODO handle type, value, traceback?
        self.event.subscribers.remove(self)
