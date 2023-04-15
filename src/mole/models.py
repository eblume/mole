# -*- coding: utf-8 -*-
from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    completed: bool = False
    labels: list[str] = field(default_factory=list)


@dataclass
class Tag:
    name: str
