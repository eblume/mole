# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import typer

from .todoist import TodoistRemote
from .models import Task

app = typer.Typer()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


@app.command()
def whack(config: Path):
    assert config.is_file()
    key = config.read_text().strip()
    assert len(key) == 40

    remote = TodoistRemote(key)

    typer.secho("🐭 Whacking moles", fg=typer.colors.GREEN)

    mole_tasks = list(remote.get_tasks(completed=False))
    typer.secho(f"🐭 Found {len(mole_tasks)} mole tasks", fg=typer.colors.YELLOW)  # TODO use inflect to pluralize


    # Catchall: there should be three primary tasks
    primary_tasks = [t for t in mole_tasks if "primary" in t.labels]
    typer.secho(f"🐭 Found {len(primary_tasks)} primary tasks", fg=typer.colors.YELLOW)
    if len(primary_tasks) != 3:
        task = Task("Pick three primary tasks", labels=["primary"])
        mole_tasks.append(task)
        remote.create_task(task)


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
