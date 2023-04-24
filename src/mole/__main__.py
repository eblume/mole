# -*- coding: utf-8 -*-
import logging

import typer

from .todoist import TodoistRemote, TodoistException
from .email import check_email
from .jira import check_jira, JiraException
from .romance import check_special_plan
from .meta import no_due_date_on_priority_item, on_deck_grooming, inbox_cleanup

app = typer.Typer()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


@app.command()
def whack():
    try:
        remote = TodoistRemote()
    except TodoistException as e:
        typer.secho(f"🐭 Error: {e}", fg=typer.colors.RED)
        return

    check_email(remote)

    try:
        check_jira(remote)
    except JiraException as e:
        typer.secho(f"🤷 Skipping Jira: {e}", fg=typer.colors.YELLOW)

    check_special_plan(remote)

    no_due_date_on_priority_item(remote)
    on_deck_grooming(remote)
    inbox_cleanup(remote)

    typer.secho("\n🐭 Done whacking moles", fg=typer.colors.GREEN)


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
