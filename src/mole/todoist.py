import json
import uuid
from typing import Optional

import requests

from .secrets import get_secret


def create_task(title: str, due: Optional[str] = None) -> int:
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

    document = {"content": title}
    if due is not None:
        document["due_string"] = due

    json_data = json.dumps(document)
    response = requests.post(
        "https://api.todoist.com/rest/v2/tasks", headers=headers, data=json_data
    )
    response.raise_for_status()
    task_id = response.json()["id"]
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
