"""Journaling module"""
from typing import Optional
import datetime as dt
from pathlib import Path

import typer

from .todoist import TodoistRemote
from .models import Task


def journal_dir() -> Path:
    journal_dir = Path.home() / 'journal'
    if not journal_dir.exists():
        typer.secho('📓 Creating journal directory', fg=typer.colors.BLUE)
        journal_dir.mkdir()
    return journal_dir


def journal_entry(when: dt.datetime) -> Path:
    """Return the filename for the journal entry"""
    return journal_dir() / f'{when:%Y-%m-%d_%HH-%MM}.md'


def journal(entry: str, when: Optional[dt.datetime]) -> None:
    """Write entry to the journal file.

    Assume today's journal entry if when is None.
    """
    when = when or dt.datetime.now()

    journal_file = journal_entry(when)
    if journal_file.exists():
        typer.secho('📓 Journal entry already exists', fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f'📓 Writing journal entry to {journal_file}', fg=typer.colors.BLUE)
    with open(journal_file, 'w') as f:
        f.write(f'# {when:%A, %B %d, %Y}\n\n')
        f.write(entry)
        f.write('\n')


def ensure_journal(remote: TodoistRemote):
    """Manage a to-do for a daily journal entry"""
    task_name = "Daily Journal"
    now = dt.datetime.now()
    existing_tasks = remote.get_tasks(project_name="Life", name=task_name)
    existing_entry = journal_entry(now)

    if len(existing_tasks) > 1:
        for extra in existing_tasks[1:]:
            typer.secho(f'📓 Deleting extra journal entry task {extra}', fg=typer.colors.RED)
            remote.delete_task(extra)

    if existing_entry.exists():
        if existing_tasks:
            typer.secho('📓 Marking journal entry task as done', fg=typer.colors.BLUE)
            # TODO complete, not delete
            remote.delete_task(existing_tasks[0])
        else:
            typer.secho('📓 Journal entry exists', fg=typer.colors.GREEN)
    else:
        if existing_tasks:
            typer.secho('📓 Journal entry task exists', fg=typer.colors.GREEN)
        else:
            typer.secho('📓 Creating journal entry task', fg=typer.colors.BLUE)
            remote.create_task(Task(task_name), project_name="Life")
