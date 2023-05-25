"""Journaling module"""
from typing import Optional
import io
import datetime as dt
from dateutil.tz import tzlocal

import typer
import boto3

from .todoist import TodoistRemote
from .models import Task
from .blumeops import boto_session


s3_resource = boto_session.resource('s3')


BUCKET_NAME = "blumeops"


def journal_entry(when: dt.date) -> str:
    """Return the key for the journal entry"""
    return f'journal/{when:%Y-%m-%d}.md'


def journal_exists(when: dt.date) -> bool:
    """Return true if the journal entry exists"""
    journal_file_key = journal_entry(when)
    try:
        s3_resource.Object(BUCKET_NAME, journal_file_key).load()  # type: ignore
        return True
    except boto3.exceptions.botocore.exceptions.ClientError as e:  # type: ignore
        if e.response['Error']['Code'] == "404":
            return False
        else:
            raise e


def write_journal(entry: str, when: Optional[dt.datetime] = None) -> None:
    """Write entry to the journal file.

    Assume current time for the journal entry if when is None.
    """
    when = when or dt.datetime.now(tzlocal())
    journal_file_key = journal_entry(when.date())
    typer.secho(f'📓 Writing journal entry to s3://{BUCKET_NAME}/{journal_file_key}', fg=typer.colors.BLUE)
    
    file = io.BytesIO()
    file.write(entry.encode())
    file.seek(0)
    
    s3_resource.Bucket(BUCKET_NAME).put_object(Body=file, Key=journal_file_key)  # type: ignore


def read_journal(when: Optional[dt.datetime] = None, add_subheading: bool = True) -> str:
    """Read the journal entry for the given date and time.

    Assume current time for the journal entry if when is None. If the entry does not exist, a new one is generated from a template,
    although the underlying file will not be created until write_journal is called.
    """
    when = when or dt.datetime.now(tzlocal())

    journal_file_key = journal_entry(when.date())
    try:
        obj = s3_resource.Object(BUCKET_NAME, journal_file_key)  # type: ignore
        file = io.BytesIO()
        obj.download_fileobj(file)
        file.seek(0)
        typer.secho(f'📓 Reading journal entry from s3://{BUCKET_NAME}/{journal_file_key}', fg=typer.colors.BLUE)
        entry = file.read().decode()
        if add_subheading:
            entry += f'\n## {when.strftime("%H:%M")}\n'
        return entry
    except boto3.exceptions.botocore.exceptions.ClientError as e:  # type: ignore
        if e.response['Error']['Code'] == "404":
            typer.secho(f'📓 Journal entry does not exist, generating from template', fg=typer.colors.BLUE)
            subheading = f'## {when.strftime("%H:%M")}\n' if add_subheading else ""
            return f'# {when.strftime("%A, %B %d, %Y")}\n{subheading}\n\n'
        else:
            raise e


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

    if existing_entry is not None:
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
