"""Modules which encode meta-process, ie ticket ceremonies, backlog grooming, etc."""

import typer

from .todoist import TodoistRemote, TodoistException
from .models import Task


# TODO obviously this cant really be a constant, so some more elastic system is needed
TARGET_MAX_DECK_SIZE = 50


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


def on_deck_grooming(remote: TodoistRemote) -> None:
    """Scans the "On Deck" (p3) and creates various meta tasks to keep it groomed.

    If any of the following are true, a "review_on_deck" label is applied and a task is created to review that label:

    - p3 tasks with no due date
    - p3 tasks that have been due for more than 3 months

    If any of the following are true, a corresponding ticket is made, and deleted if not:

    - # of p3 tasks > TARGET_MAX_DECK_SIZE
    """
    check_task_name = "Review On Deck: Check 'review_on_deck' label"
    check_tasks = remote.get_tasks(name=check_task_name)
    filter = "p3 & (no date | due before: -3 months)"
    tasks = remote.get_tasks(filter=filter)
    if len(tasks) > 0:
        for task in tasks:
            if "review_on_deck" not in task.labels:
                task.labels.add("review_on_deck")
                remote.update_task(task)

        if len(check_tasks) == 0:
            remote.create_task(Task(name=check_task_name), project_name="Meta")
    else:
        if len(check_tasks) > 0:
            remote.delete_task(check_tasks[0])


def inbox_cleanup(remote: TodoistRemote) -> None:
    """Keep the inbox clear - all tasks should be assigned to a project."""
    inbox_tasks = remote.get_tasks(project_name="Inbox", filter="no date")
    inbox_cleanup_task_name = "Inbox Cleanup"
    inbox_cleanup_tasks = remote.get_tasks(name=inbox_cleanup_task_name)

    # Clean up extras
    for task in inbox_tasks[1:]:
        remote.delete_task(task)
        typer.secho(f"🗑️  Deleted extra {task.name}", fg=typer.colors.YELLOW)

    if len(inbox_tasks) > 0:
        if len(inbox_cleanup_tasks) == 0:
            remote.create_task(Task(name=inbox_cleanup_task_name), project_name="Meta")
        else:
            typer.secho(f"✅ {inbox_cleanup_task_name}", fg=typer.colors.GREEN)
    else:
        if len(inbox_cleanup_tasks) > 0:
            remote.delete_task(inbox_cleanup_tasks[0])
