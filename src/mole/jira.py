import os
from jira import JIRA, Issue

from .todoist import TodoistRemote
from .models import Task


API_KEY = os.getenv('JIRA_APPLICATION_KEY')
URL = os.getenv('JIRA_SERVER_URL')


def get_my_issues() -> dict[str, str]:
    assert URL
    assert API_KEY

    jira = JIRA(server=URL, token_auth=API_KEY) 
    issues = jira.search_issues('assignee = currentUser()')

    # Why does mypy think issues can be strs? search_issues may need checking. TODO
    return {issue.key: issue.fields.summary for issue in issues if isinstance(issue, Issue)}


def check_jira(remote: TodoistRemote) -> None:
    """Update tasks based on Jira status"""
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
        remote.create_task(Task(key, labels=["jira"]))

