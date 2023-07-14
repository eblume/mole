from __future__ import annotations
import os
import datetime as dt

from dataclasses import dataclass, field
import requests
import typer

from todoist_api_python.api import TodoistAPI

from .models import Task, CompletedTask


class TodoistException(Exception):
    pass


@dataclass
class TodoistRemote:
    default_project_name: str = "Hermes"  # TODO this probably isnt how I want to specify this

    api: TodoistAPI = field(init=False)
    default_project_id: str = field(init=False)
    project_map: dict[str, str] = field(init=False)
    project_id_map: dict[str, str] = field(init=False)

    def __post_init__(self):
        api_key = os.environ.get("TODOIST_API_KEY")
        if api_key is None or len(api_key) != 40:
            raise TodoistException("TODOIST_API_KEY must be set to a valid API key")
        self.api = TodoistAPI(api_key)
        all_projects = self.api.get_projects()
        default_projects = [p for p in all_projects if p.name == self.default_project_name]
        assert len(default_projects) == 1  # TODO handle this better. Maybe create the project if it doesn't exist?
        self.default_project_id = default_projects[0].id
        self.project_map = {}
        for project in all_projects:
            self.project_map[project.name] = project.id
        self.project_id_map = {v: k for k, v in self.project_map.items()}

    def get_tasks(
        self,
        name: str | None = None,
        project_name: str | None = None,
        filter: str | None  = None,
        label: str | None  = None
    ) -> list[Task]:
        project_id = self.project_map[project_name] if project_name is not None else None

        # BUG: Searching by label fails, but you can use filters. This is a bug in the todoist api.
        # TODO report this
        # Workaround: push label to filter unless filter has been provided already, in which case raise an error (for
        # now)
        if label is not None:
            if filter is not None:
                raise TodoistException("Cannot provide both filter and label")
            filter = f"@{label}"

        todoist_tasks = self.api.get_tasks(project_id=project_id, filter=filter)

        def _filt(task):
            if name is None:
                return True
            return task.content == name

        return [
            Task(
                name=todoist_task.content,
                id=todoist_task.id,
                labels=set(todoist_task.labels),
                due=todoist_task.due,
                project_id=todoist_task.project_id,
                description=todoist_task.description,
                priority=todoist_task.priority
            )
            for todoist_task in todoist_tasks
            if _filt(todoist_task)
        ]

    def create_task(self, task: Task, project_name: str | None  = None):
        """Create a task in the default project, or in the project specified by project_name.

        The order of preference for project is:
          1. project_name in kwargs (which is resolved to a project id by this function)
          2. task.project_id
          3. self.default_project_id
        """
        typer.secho(f"🆕 Creating task: {task.name}", fg=typer.colors.BRIGHT_BLUE)
        if project_name is not None:
            project_id = self.project_map[project_name]
        else:
            project_id = task.project_id or self.default_project_id

        # Default due_date to today, we may want to change this later
        # TODO see note in models.py about 'due problem'
        due_date = dt.date.today().strftime("%Y-%m-%d")

        self.api.add_task(task.name, project_id=project_id, labels=list(task.labels), due_date=due_date, description=task.description, priority=task.priority)

    def delete_task(self, task: Task):
        typer.secho(f"🗑  Deleting task: {task.name}", fg=typer.colors.BRIGHT_BLUE)

        # If we have the task id already, this is easy
        if task.id is not None:
            self.api.delete_task(task.id)
            return

        # The hard eay:
        todoist_tasks = self.api.get_tasks()  # TODO this does not scale
        todoist_tasks = [t for t in todoist_tasks if t.content == task.name]
        assert len(todoist_tasks) > 0
        todoist_task = todoist_tasks[0]  # Pick the first. TODO: handle multiple tasks with the same name more gracefully.
        self.api.delete_task(todoist_task.id)

    def update_task(self, task: Task):
        if task.id is None:
            raise TodoistException("Cannot update task without an id")

        typer.secho(f"🔄 Updating task: {task.name}", fg=typer.colors.BRIGHT_BLUE)
        self.api.update_task(task.id, content=task.name, due=task.due, labels=list(task.labels), description=task.description, priority=task.priority)

    def get_completed_tasks(self, project_id: int | None = None, limit: int = 200, since: dt.datetime | None = None) -> list[CompletedTask]:
        """Get completed tasks from the todoist API."""
        # Uses v9 sync API, because the rest API doesnt support completed tasks
        # TODO this entire module aught to move to sync API, no?
        # TODO offset / limit for pagination
        headers = { 'Authorization: Bearer': os.environ.get("TODOIST_API_KEY") }
        params = { 'annotate_notes': False }
        if project_id:
            params['project_id'] = project_id  # type: ignore
        if limit:
            params['limit'] = limit  # type: ignore
        if since:
            # Doc format example: 2007-04-29T10:13 -- almost isoformat?
            # TODO handle TZ, I guess? Maybe just use isoformat?
            params['since'] = since.strftime('%Y-%m-%dT%H:%M')  # type: ignore

        response = requests.get(
            'https://api.todoist.com/sync/v9/completed/get_all',
            headers=headers,  # type: ignore
            params=params
        )

        assert response.status_code == 200
        data = response.json()
        tasks = []
        for item in data['items']:
            tasks.append(CompletedTask(**item))
        return tasks
