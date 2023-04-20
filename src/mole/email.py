from __future__ import annotations

import subprocess
import tempfile

import typer

from .models import Task
from .todoist import TodoistRemote

GET_EMAIL_COUNT_APPLESCRIPT = """
tell application "Mail"
    set checkAccount to account "{account}"
    set checkInbox to mailbox "{inbox}" of checkAccount
    set unread to (messages of checkInbox whose read status is false)
    set countUnread to count of unread
    return countUnread
end tell

"""


# A mapping of email account names in Mail.app to the name of the inbox to check.
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
    ## Module: Check Email
    email_task_name = "Check Email"
    search_filter = "(today | overdue)"
    check_email_tasks = list(remote.get_tasks(name=email_task_name, filter=search_filter))
    email_count = sum(get_email_count(acct, inbox) for acct, inbox in EMAIL_ACCOUNTS.items())

    # First, close extra tasks
    if len(check_email_tasks) > 1:
        for task in check_email_tasks[1:]:
            remote.delete_task(task)
        check_email_tasks = check_email_tasks[:1]

    # Then, create or update the task
    if len(check_email_tasks) == 0:
        if email_count > 0:
            remote.create_task(Task(email_task_name))
    else:
        if email_count > 0:
            typer.secho(f"📬 Found an existing '{email_task_name}' task", fg=typer.colors.BLUE)
        else:
            for task in check_email_tasks:
                remote.delete_task(task)
