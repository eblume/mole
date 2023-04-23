# -*- coding: utf-8 -*-
from __future__ import annotations

from todoist_api_python.models import Due

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    name: str
    id: Optional[str] = None
    completed: bool = False
    description: Optional[str] = None
    labels: set[str] = field(default_factory=set)
    project_id: Optional[str] = None
    due: Optional[Due] = None


@dataclass
class Tag:
    name: str
