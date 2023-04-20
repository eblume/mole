from __future__ import annotations
import os
from typing import Optional
import datetime as dt

from dataclasses import dataclass, field
import typer

from todoist_api_python.api import TodoistAPI

from .models import Task


class TodoistException(Exception):
    pass


@dataclass
class TodoistRemote:
    base_project_name: str = "Hermes"  # TODO this probably isnt how I want to specify this

    api: TodoistAPI = field(init=False)
    base_project_id: str = field(init=False)

    def __post_init__(self):
        api_key = os.environ.get("TODOIST_API_KEY")
        if api_key is None or len(api_key) != 40:
            raise TodoistException("TODOIST_API_KEY must be set to a valid API key")

        self.api = TodoistAPI(api_key)
        base_projects = [p for p in self.api.get_projects() if p.name == self.base_project_name]
        assert len(base_projects) == 1  # TODO handle this better. Maybe create the project if it doesn't exist?
        self.base_project_id = base_projects[0].id

    def get_tasks(self, name: Optional[str] = None, filter: Optional[str] = None, label: Optional[str] = None) -> list[Task]:
        todoist_tasks = self.api.get_tasks(project_id=self.base_project_id, label=label, filter=filter)

        def _filt(task):
            if name is None:
                return True
            return task.content == name

        return [
            Task(todoist_task.content, labels=todoist_task.labels)
            for todoist_task in todoist_tasks
            if _filt(todoist_task)
        ]

    def create_task(self, task: Task):
        typer.secho(f"🆕 Creating task: {task.name}", fg=typer.colors.BRIGHT_BLUE)
        
        # Default due_date to today, we may want to change this later
        due_date = dt.date.today().strftime("%Y-%m-%d")

        self.api.add_task(task.name, project_id=self.base_project_id, labels=task.labels, due_date=due_date)

    def delete_task(self, task: Task):
        typer.secho(f"🗑 Deleting task: {task.name}", fg=typer.colors.BRIGHT_BLUE)
        todoist_tasks = self.api.get_tasks(project_id=self.base_project_id)
        todoist_tasks = [t for t in todoist_tasks if t.content == task.name]
        assert len(todoist_tasks) > 0
        todoist_task = todoist_tasks[0]  # Pick the first. TODO: handle multiple tasks with the same name more gracefully.
        self.api.delete_task(todoist_task.id)
