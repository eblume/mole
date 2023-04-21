# -*- coding: utf-8 -*-
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    completed: bool = False
    description: Optional[str] = None
    labels: list[str] = field(default_factory=list)
    project_id: Optional[str] = None


@dataclass
class Tag:
    name: str
