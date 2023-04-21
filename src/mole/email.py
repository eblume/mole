from __future__ import annotations

import subprocess
import tempfile

import typer

from .models import Task
from .todoist import TodoistRemote

GET_EMAIL_COUNT_APPLESCRIPT = """
try
    tell application "Mail"
        set checkAccount to account "{account}"
        set checkInbox to mailbox "{inbox}" of checkAccount
        set unread to (messages of checkInbox whose read status is false)
        set countUnread to count of unread
        return countUnread
    end tell
on error
    return -1
end try
"""

# A mapping of email account names in Mail.app to the name of the inbox to check.
# TODO make this a config or something, "checked inboxes" or some such, and search for inbox names
EMAIL_ACCOUNTS = {
    "Google": "INBOX",
    "Exchange": "Inbox"
}


def run_applescript(script: str) -> str:
    with tempfile.NamedTemporaryFile(suffix='.scpt', mode='w') as temp_file:
        temp_file.write(script)
        temp_file.flush()
        return subprocess.check_output(['osascript', temp_file.name]).decode('utf-8')


def get_email_count(account: str, inbox: str) -> int:
    """Return the number of unread emails in the inbox, using Mail.app via AppleScript"""
    script = GET_EMAIL_COUNT_APPLESCRIPT.format(account=account, inbox=inbox)
    output = run_applescript(script).strip()
    count = int(output)
    typer.secho(f"📬 [{account}/{inbox}] {count}", fg=typer.colors.GREEN if count == 0 else typer.colors.BLUE)
    return count


def check_email(remote: TodoistRemote) -> None:
    """Check for unread emails and update Todoist accordingly"""
    for account, inbox in EMAIL_ACCOUNTS.items():
        task_name = f"Check Email: {account}"
        search_filter = "(today | overdue)"
        existing_tasks = list(remote.get_tasks(name=task_name, filter=search_filter))

        email_count = get_email_count(account, inbox)

        if email_count == -1:
            typer.secho(f"🤷 Skipping missing account/inbox: [{account}/{inbox}]", fg=typer.colors.YELLOW)
            continue

        if len(existing_tasks) > 1:
            for task in existing_tasks[1:]:
                remote.delete_task(task)
            existing_tasks = existing_tasks[:1]

        if len(existing_tasks) == 0:
            if email_count > 0:
                remote.create_task(Task(task_name))
            else:
                typer.secho(f"📬 Nothing to do for [{account}/{inbox}]", fg=typer.colors.GREEN)
        else:
            if email_count > 0:
                typer.secho(f"📬 Found an existing '{task_name}' task", fg=typer.colors.BLUE)
            else:
                for task in existing_tasks:
                    remote.delete_task(task)
