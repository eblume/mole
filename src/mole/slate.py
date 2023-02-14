# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import auto, Enum
from typing import Optional

from .task import Task


class SlateTaskStatus(Enum):
    unknown = auto()
    created = auto()
    removed = auto()


class Slate:
    pass


class UnsolvedSlate(Slate):
    pass


@dataclass
class SolvedSlate(Slate):
    tasks: list[Task] = field(default_factory=list)

    def compare(self, tasks: list[Task]) -> Iterable[tuple[Task, SlateTaskStatus]]:
        tasks_by_name = {t.name: [t] for t in self.tasks}
        self_tasks = dict(tasks_by_name)  # Keep a copy for comparison

        for task in tasks:
            if task.name not in tasks_by_name:
                tasks_by_name[task.name] = [task]
            else:
                tasks_by_name[task.name].append(task)

        for name, tasks in tasks_by_name.items():
            condensed_task = self._condense_tasks(tasks)
            assert (
                condensed_task is not None
            )  # Should not be possible, logically, so find a better way to express?
            if name not in self_tasks:
                status = SlateTaskStatus.unknown
            else:
                status = SlateTaskStatus.created
            yield condensed_task, status

    def _condense_tasks(self, tasks: list[Task]) -> Optional[Task]:
        if len(tasks) == 0:
            return None
        elif len(tasks) == 1:
            return tasks[0]
        else:
            # TODO we need to be MUCH smarter about this.
            # For now, just return the second task, and in the future, maybe do something like seperate out tasks from
            # task defenitions.
            return tasks[1]
