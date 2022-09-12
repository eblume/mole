# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field, InitVar
from typing import TYPE_CHECKING

from .events import Subscription

if TYPE_CHECKING:
    from .engine import Engine
    from .models import Task


@dataclass
class ItemEventPrinter:
    engine: InitVar[Engine]
    subcription: Subscription[Task] = field(init=False)

    def __post_init__(self, engine: Engine):
        self.subscription = engine.events.NEW_TASK.subscribe()

    async def run(self) -> None:
        with self.subscription as read_queue:
            while True:
                task = await read_queue.get()
                print(f"New task: {task.name}")
