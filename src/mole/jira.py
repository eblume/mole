import textwrap
import typer
import os

from jira import JIRA, Issue

from .todoist import TodoistRemote
from .models import Task
from .vpn import is_vpn_connected


API_KEY = os.getenv('JIRA_APPLICATION_KEY')
URL = os.getenv('JIRA_SERVER_URL')


class JiraException(Exception):
    pass


def ensure_jira_ready():
    if not URL:
        raise JiraException("JIRA_SERVER_URL must be set")
    elif not API_KEY:
        raise JiraException("JIRA_APPLICATION_KEY must be set")
    elif not is_vpn_connected():
        raise JiraException("VPN must be connected")


def get_my_issues() -> dict[str, str]:
    assert URL is not None  # checked by ensure_jira_ready
    jira = JIRA(server=URL, token_auth=API_KEY) 
    typer.secho(f"🔍 Fetching Jira issues", fg=typer.colors.YELLOW)
    issues = jira.search_issues('assignee = currentUser()')

    # Why does mypy think issues can be strs? search_issues may need checking. TODO
    return {issue.key: issue.fields.summary for issue in issues if isinstance(issue, Issue)}


def check_jira(remote: TodoistRemote) -> None:
    """Update tasks based on Jira status"""
    ensure_jira_ready()

    work_tasks_in_jira = get_my_issues()
    work_tasks_in_todoist = { t.name: t for t in remote.get_tasks(filter="(today | overdue)", label="jira")}

    name_to_jira_task = { make_name(key, summary): key for key, summary in work_tasks_in_jira.items() }

    extra_tasks = set(work_tasks_in_todoist.keys()) - set(name_to_jira_task.keys())
    new_tasks = set(name_to_jira_task.keys()) - set(work_tasks_in_todoist.keys())

    if extra_tasks:
        typer.secho(f"🔍 Found {len(extra_tasks)} extra tasks in Todoist", fg=typer.colors.BLUE)

    if new_tasks:
        typer.secho(f"🔍 Found {len(new_tasks)} new tasks in Jira", fg=typer.colors.BLUE)

    if not extra_tasks and not new_tasks:
        # check mark emoji is: ✔️
        typer.secho("✔️ No Jira changes found", fg=typer.colors.GREEN)

    # First, close extra tasks
    for task_name in extra_tasks:
        remote.delete_task(work_tasks_in_todoist[task_name])

    # Second, create missing tasks
    for name in new_tasks:
        task = name_to_jira_task[name]
        ticket_url = f"{URL}/browse/{task}"
        remote.create_task(Task(name, labels=["jira"], description=ticket_url), project_name="Work")


def make_name(ticket: str, summary: str) -> str:
    return textwrap.shorten(f"{ticket}: {summary}", width=100, placeholder="...")
