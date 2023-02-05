# -*- coding: utf-8 -*-
from dataclasses import dataclass, field

from .task import Task


@dataclass
class Actions:
    create_task: list[Task] = field(default_factory=list)
