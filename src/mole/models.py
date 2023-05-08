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
    # TODO there is a 'due problem', related to a 'project problem', and the root of it is that this model is trying to
    # pull double duty as a container for todoist task creation API as well as a representation of the state of tasks
    # inside and outside of Todoist. There needs to be a rethinking of the model layer and the API layer and how data
    # gets shuttled between them. At this moment I am thinking that the todoist.py API layer should NOT use models and
    # instead should build them. Anyway the upshot is that if you are creating a new Task, this 'due' field is entirely
    # ignored.
    due: Optional[Due] = None
    priority: int = 4


@dataclass
class Tag:
    name: str
