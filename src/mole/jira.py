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
    issues = jira.search_issues('assignee = currentUser()')

    # Why does mypy think issues can be strs? search_issues may need checking. TODO
    return {issue.key: issue.fields.summary for issue in issues if isinstance(issue, Issue)}


def check_jira(remote: TodoistRemote) -> None:
    """Update tasks based on Jira status"""
    ensure_jira_ready()
    issues = get_my_issues()
    jira_tasks = {t.name: t for t in remote.get_tasks(filter="(today | overdue)", label="jira")}
    extra_tasks = set(jira_tasks.keys()) - set(issues.keys())
    new_issues = set(issues.keys()) - set(jira_tasks.keys())

    # First, close extra tasks
    for task_name in extra_tasks:
        remote.delete_task(jira_tasks[task_name])

    # Second, create missing tasks
    for key in new_issues:
        # TODO add description, link, etc.
        remote.create_task(Task(key, labels=["jira"]), project_name="Work")

