# -*- coding: utf-8 -*-
import logging

import typer
import datetime as dt

from .todoist import TodoistRemote, TodoistException
from .email import check_email
from .jira import check_jira, JiraException
from .romance import check_special_plan
from .meta import no_due_date_on_priority_item, on_deck_grooming, inbox_cleanup
from .journal import ensure_journal, write_journal, read_journal

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
    ensure_journal(remote)

    typer.secho("\n🐭 Done whacking moles", fg=typer.colors.GREEN)


@app.command()
def journal():
    """Write a journal entry using $EDITOR"""
    # Run $EDITOR and return the result
    # TODO this isn't quite right. Instead of a new file every time, it should open the same day's file each time.
    today = dt.datetime.now().date()
    entry = typer.edit(read_journal(today), extension='.md', require_save=True)

    if entry is None:
        typer.secho('📓 No journal entry written', fg=typer.colors.YELLOW)
        return

    write_journal(entry, today)


@app.command()
def game():
    """Tell OpenAI to play a game. Requires OPENAI_API_KEY to be set.

    STATUS: Not yet working. Basic pattern is mostly there, but need to switch from Completion api to Chat.Completion
    API, not sure why.
    """
    import os, openai
    from .game import Game, Player

    openai.api_key = os.getenv('OPENAI_API_KEY')

    game = Game(Player())
    game.run()


@app.command()
def summary(temperature: float = 0.3, extra_prompt: str = ""):
    """Get an LLM summary of the day"""
    import openai, os
    openai.api_key = os.getenv('OPENAI_API_KEY')

    from .summary import get_summary
    typer.echo(get_summary(temperature=temperature, extra_prompt=extra_prompt))


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
