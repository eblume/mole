# -*- coding: utf-8 -*-
import logging

import typer

from .todoist import TodoistRemote
from .models import Task
from .email import get_email_count

app = typer.Typer()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# A mapping of email account names in Mail.app to the name of the inbox to check.
EMAIL_ACCOUNTS = {
    "Google": "INBOX",
    "Exchange": "Inbox"
}


@app.command()
def whack():
    remote = TodoistRemote()

    ## Module: Check Email
    # Filter: is there a task called "Check Email"?
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

    typer.secho("\n🐭 Done whacking moles", fg=typer.colors.GREEN)


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
