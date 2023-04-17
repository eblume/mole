from __future__ import annotations
import os

from dataclasses import dataclass, field
from typing import Iterable, Optional
import typer

from todoist_api_python.api import TodoistAPI

from .models import Task


@dataclass
class TodoistRemote:
    base_project_name: str = "Hermes"  # TODO this probably isnt how I want to specify this

    api: TodoistAPI = field(init=False)
    base_project_id: str = field(init=False)

    def __post_init__(self):
        api_key = os.environ.get("TODOIST_API_KEY")
        assert api_key and len(api_key) == 40
        self.api = TodoistAPI(api_key)
        base_projects = [p for p in self.api.get_projects() if p.name == self.base_project_name]
        assert len(base_projects) == 1  # TODO handle this better. Maybe create the project if it doesn't exist?
        self.base_project_id = base_projects[0].id

    def get_tasks(self, completed: Optional[bool] = None) -> Iterable[Task]:
        for task in self.api.get_tasks(project_id=self.base_project_id):
            if completed is None or task.is_completed == completed:
                yield Task(task.content, completed=task.is_completed, labels=task.labels)

    def create_task(self, task: Task):
        typer.secho(f"🆕 Creating task: {task.name}", fg=typer.colors.BRIGHT_BLUE)
        self.api.add_task(task.name, project_id=self.base_project_id, labels=task.labels)
