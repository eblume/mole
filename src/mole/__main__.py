# -*- coding: utf-8 -*-
import logging

import typer

from .todoist import TodoistRemote
from .models import Task

app = typer.Typer()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


@app.command()
def whack():
    remote = TodoistRemote()

    typer.secho("🐭 Whacking moles", fg=typer.colors.GREEN)

    mole_tasks = list(remote.get_tasks(completed=False))
    typer.secho(f"🐭 Found {len(mole_tasks)} mole tasks", fg=typer.colors.YELLOW)  # TODO use inflect to pluralize

    # Final Catchall: If we've still got no tasks, make a basic "Work on Mole" task.
    if len(mole_tasks) == 0:
        remote.create_task(Task("Work on mole", labels=["primary"]))

    typer.secho("🐭 Done whacking moles", fg=typer.colors.GREEN)


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
