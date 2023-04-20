# -*- coding: utf-8 -*-
import logging

import typer

from .todoist import TodoistRemote
from .models import Task
from .email import check_email
from .jira import check_jira

app = typer.Typer()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


@app.command()
def whack():
    remote = TodoistRemote()
    check_email(remote)
    check_jira(remote)
    typer.secho("\n🐭 Done whacking moles", fg=typer.colors.GREEN)


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
