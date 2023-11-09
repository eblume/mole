import requests
import json
import uuid


from .secrets import get_secret


def create_task(title: str) -> str:
    """Create a new task in Todoist with the given title, returning a todoist:// url.

    Task will be created as due today and will be left in the inbox.

    Credentials are retrieved from 1password from the 'blumeops' vault.
    """
    key = get_secret("Todoist", "credential", vault="blumeops")

    headers = {
        "Authorization": f"Bearer {key}",
        "X-Requerst-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }

    json_data = json.dumps(
        {
            "content": title,
            "due_string": "today",
        }
    )

    response = requests.post("https://api.todoist.com/rest/v2/tasks", headers=headers, data=json_data)
    response.raise_for_status()
    url = response.json()["url"]
    return url.replace("https://todoist.com/showTask?", "todoist://task?")
