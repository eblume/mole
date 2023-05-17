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

def inbox_cleanup(remote: TodoistRemote) -> None:
    """Keep the inbox clear - all tasks should be assigned to a project."""
    inbox_tasks = remote.get_tasks(project_name="Inbox", filter="no date")
    inbox_cleanup_task_name = "Inbox Cleanup"
    inbox_cleanup_tasks = remote.get_tasks(name=inbox_cleanup_task_name)

    # Clean up extras
    for task in inbox_cleanup_tasks[1:]:
        remote.delete_task(task)
        typer.secho(f"🗑️  Deleted extra {task.name}", fg=typer.colors.YELLOW)

    if len(inbox_tasks) > 0:
        if len(inbox_cleanup_tasks) == 0:
            remote.create_task(Task(name=inbox_cleanup_task_name), project_name="Meta")
        else:
            typer.secho(f"✅ '{inbox_cleanup_task_name}' task found", fg=typer.colors.GREEN)
    else:
        if len(inbox_cleanup_tasks) > 0:
            remote.delete_task(inbox_cleanup_tasks[0])
