import textwrap
from typing import Dict

import typer
from jira import JIRA, Issue

from .models import Task
from .todoist import TodoistRemote
from .vpn import is_vpn_connected
from .credentials import jira_key, jira_hostname


class JiraException(Exception):
    pass


def ensure_jira_ready() -> None:
    if not jira_hostname():
        raise JiraException("Jira server hostname must be set in 1Password")
    elif not jira_key():
        raise JiraException("Jira API key must be set in 1Password")
    elif not is_vpn_connected():
        raise JiraException("VPN must be connected")


def get_my_issues() -> Dict[str, str]:
    jira = JIRA(server=f"https://{jira_key()}/jira", token_auth=jira_key())
    typer.secho("🔍 Fetching Jira issues", fg=typer.colors.YELLOW)
    issues = jira.search_issues("assignee = currentUser()")

    return {issue.key: issue.fields.summary for issue in issues if isinstance(issue, Issue)}


def check_jira(remote: TodoistRemote) -> None:
    """Update tasks based on Jira status."""
    ensure_jira_ready()

    jira_tasks = get_my_issues()
    todoist_tasks = {
        task.name: task for task in remote.get_tasks(filter="(today | overdue) & @jira")
    }

    name_to_jira_task = {make_name(key, summary): key for key, summary in jira_tasks.items()}

    extra_tasks = set(todoist_tasks.keys()) - set(name_to_jira_task.keys())
    new_tasks = set(name_to_jira_task.keys()) - set(todoist_tasks.keys())

    if extra_tasks:
        typer.secho(f"🔍 Found {len(extra_tasks)} extra tasks in Todoist", fg=typer.colors.BLUE)

    if new_tasks:
        typer.secho(f"🔍 Found {len(new_tasks)} new tasks in Jira", fg=typer.colors.BLUE)

    if not extra_tasks and not new_tasks:
        typer.secho("✔️ No Jira changes found", fg=typer.colors.GREEN)

    # First, close extra tasks
    for task_name in extra_tasks:
        remote.delete_task(todoist_tasks[task_name])

    # Second, create missing tasks
    for name in new_tasks:
        task = name_to_jira_task[name]
        ticket_url = f"https://{jira_hostname()}/jira/browse/{task}"
        remote.create_task(Task(name, labels={"jira"}, description=ticket_url), project_name="Work")


def make_name(ticket: str, summary: str) -> str:
    return textwrap.shorten(f"{ticket}: {summary}", width=100, placeholder="...")
