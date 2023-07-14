# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path

import typer

from .todoist import TodoistRemote, TodoistException
from .email import check_email
from .jira import check_jira, JiraException
from .romance import check_special_plan
from .meta import no_due_date_on_priority_item, inbox_cleanup
from .journal import ensure_journal, write_journal, read_journal
from .blumeops import require_blumeops

app = typer.Typer(
    help="Mole is a tool for automating my life.",
    no_args_is_help=True,
)

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
    inbox_cleanup(remote)
    ensure_journal(remote)

    typer.secho("\n🐭 Done whacking moles", fg=typer.colors.GREEN)


@app.command()
@require_blumeops
def journal(startinsert: bool = typer.Option(True, "--startinsert/--no-startinsert", help="Start in insert mode on the last line")):
    """Write a journal entry using $EDITOR"""
    editor = os.getenv('EDITOR', None)
    if not editor:
        # Not strictly necessary as I think typer.edit will still function, however, in my case it is always an error
        # and I want to know about it. It also breaks the vim startmode.
        typer.secho('📓 No $EDITOR set, cannot write journal entry', fg=typer.colors.RED)
        return

    if startinsert and Path(editor).name in ['vim', 'nvim', 'vi']:
        # Start in insert mode on the last line
        editor += ' -c "normal Go" -c "startinsert"'

    entry = typer.edit(read_journal(), extension='.md', require_save=True, editor=editor)

    if entry is None:
        typer.secho('📓 No journal entry written', fg=typer.colors.YELLOW)
        return

    write_journal(entry)


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
