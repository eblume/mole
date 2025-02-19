import uuid
from typing import Optional

import requests
from pydantic import BaseModel

from .secrets import get_secret


class TodoistTaskDefinition(BaseModel):
    id: int
    creator_id: int
    created_at: str
    assignee_id: Optional[int]
    assigner_id: Optional[int]
    comment_count: int
    is_completed: bool
    content: str
    description: str
    due: Optional[dict]
    deadline: Optional[dict]
    duration: Optional[dict]
    labels: list[str]
    order: int
    priority: int
    project_id: int
    section_id: Optional[int]
    parent_id: Optional[int]
    url: str


class TodoistTaskCreate(BaseModel):
    content: str
    due_string: Optional[str] = None
    labels: Optional[list[str]] = None


def create_task(
    title: str, due: Optional[str] = None, labels: Optional[list[str]] = None
) -> int:
    """Create a new task in Todoist with the given title, returning the task ID as an integer.

    Task will be created as due today by default and will be left in the inbox.

    Credentials are retrieved from 1password from the 'blumeops' vault.
    """
    key = get_secret("Todoist", "credential", vault="blumeops")

    headers = {
        "Authorization": f"Bearer {key}",
        "X-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

    document = TodoistTaskCreate(content=title, due_string=due, labels=labels)
    json_data = document.model_dump_json(exclude_unset=True)
    response = requests.post(
        "https://api.todoist.com/rest/v2/tasks", headers=headers, data=json_data
    )
    response.raise_for_status()
    task_id = int(response.json()["id"])
    return task_id


def delete_task(task_id: int) -> None:
    """Delete a task in Todoist by its ID."""
    key = get_secret("Todoist", "credential", vault="blumeops")
    headers = {"Authorization": f"Bearer {key}"}
    print(f"Deleting task with ID: {task_id}")
    print(f"Request URL: https://api.todoist.com/rest/v2/tasks/{task_id}")
    response = requests.delete(
        f"https://api.todoist.com/rest/v2/tasks/{task_id}", headers=headers
    )
    response.raise_for_status()


def task_exists(task_id: int) -> bool:
    """Check if a task exists in Todoist by its ID."""
    key = get_secret("Todoist", "credential", vault="blumeops")
    headers = {"Authorization": f"Bearer {key}"}
    response = requests.get(
        f"https://api.todoist.com/rest/v2/tasks/{task_id}", headers=headers
    )
    return response.status_code != 404


def get_task(task_id: int) -> TodoistTaskDefinition:
    """Retrieve a task from Todoist by its ID and return its details as a Task model."""
    key = get_secret("Todoist", "credential", vault="blumeops")
    headers = {"Authorization": f"Bearer {key}"}
    response = requests.get(
        f"https://api.todoist.com/rest/v2/tasks/{task_id}", headers=headers
    )
    response.raise_for_status()
    return TodoistTaskDefinition(**response.json())
