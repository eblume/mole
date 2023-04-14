# -*- coding: utf-8 -*-
import logging
from pathlib import Path

import typer

from .todoist import TodoistRemote
from .models import Task

app = typer.Typer()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.DEBUG
)


@app.command()
def whack(config: Path):
    assert config.is_file()
    key = config.read_text().strip()
    assert len(key) == 40

    remote = TodoistRemote(key)

    typer.secho("🐭 Whacking moles", fg=typer.colors.GREEN)

    mole_tasks = list(remote.get_tasks(completed=False))
    if len(mole_tasks) == 0:
        remote.create_task(Task("Work on mole"))
    else:
        typer.secho(f"🐭 Found {len(mole_tasks)} mole tasks", fg=typer.colors.YELLOW)  # TODO use inflect to pluralize

    typer.secho("🐭 Done whacking moles", fg=typer.colors.GREEN)


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
