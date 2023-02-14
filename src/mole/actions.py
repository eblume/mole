# -*- coding: utf-8 -*-
from dataclasses import dataclass, field

from .task import Task


@dataclass
class Actions:
    create_task: list[Task] = field(default_factory=list)
    delete_task: list[Task] = field(default_factory=list)

    def __len__(self) -> int:
        """Return count of all actions across all types"""
        return len(self.create_task) + len(self.delete_task)
