"""Journaling module"""
from typing import Optional
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

import typer

from .todoist import TodoistRemote
from .models import Task


def journal_dir() -> Path:
    journal_dir = Path.home() / 'journal'
    if not journal_dir.exists():
        typer.secho('📓 Creating journal directory', fg=typer.colors.BLUE)
        journal_dir.mkdir()
    return journal_dir


def journal_entry(when: dt.date) -> Path:
    """Return the filename for the journal entry"""
    return journal_dir() / f'{when:%Y-%m-%d}.md'


def write_journal(entry: str, when: Optional[dt.date] = None) -> Path:
    """Write entry to the journal file.

    Assume today's journal entry if when is None.
    """
    when = when or dt.datetime.now(ZoneInfo('local')).date()
    journal_file = journal_entry(when)
    typer.secho(f'📓 Writing journal entry to {journal_file}', fg=typer.colors.BLUE)
    journal_file.write_text(entry)
    return journal_file


def read_journal(when: Optional[dt.date] = None) -> str:
    """Read the journal entry for the given date.

    Assume today's journal entry if when is None. If the entry does not exist, a new one is generated from a template,
    although the underlying file will not be created until write_journal is called.
    """
    when = when or dt.datetime.now(ZoneInfo('local')).date()

    journal_file = journal_entry(when)
    if journal_file.exists():
        typer.secho(f'📓 Reading journal entry from {journal_file}', fg=typer.colors.BLUE)
        return journal_file.read_text()

    typer.secho(f'📓 Journal entry does not exist, generating from template', fg=typer.colors.BLUE)
    return f'# {when:%A, %B %d, %Y}\n\n'


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
            # TODO complete, not delete
            remote.delete_task(existing_tasks[0])
        else:
            typer.secho('📓 Journal entry exists', fg=typer.colors.GREEN)
    else:
        if existing_tasks:
            typer.secho('📓 Journal entry task exists', fg=typer.colors.GREEN)
        else:
            remote.create_task(Task(task_name), project_name="Life")
