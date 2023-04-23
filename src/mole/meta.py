"""Modules which encode meta-process, ie ticket ceremonies, backlog grooming, etc."""

import typer

from .todoist import TodoistRemote
from .models import Task


def no_due_date_on_priority_item(remote: TodoistRemote) -> None:
    """Check that priority items have a due date."""
    check_filter = "(p1 | p2 | p3) & no date"
    tasks = remote.get_tasks(filter=check_filter)
    check_task_name = "Check that priority items have a due date"
    check_tasks = remote.get_tasks(name=check_task_name)
    if len(tasks) > 0:
        if len(check_tasks) == 0:
            remote.create_task(Task(name=check_task_name), project_name="Meta")
        else:
            typer.secho(f"✅ {check_task_name}", fg=typer.colors.GREEN)
    else:
        if len(check_tasks) > 0:
            remote.delete_task(check_tasks[0])

