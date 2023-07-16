# -*- coding: utf-8 -*-
import logging
import os
import sys
from pathlib import Path

import typer
import requests

from .todoist import TodoistRemote, TodoistException
from .email import check_email
from .jira import check_jira, JiraException
from .romance import check_special_plan
from .meta import no_due_date_on_priority_item, inbox_cleanup
from .journal import ensure_journal, write_journal, read_journal
from .blumeops import require_blumeops, has_blumeops_profile
from .credentials import get_item


app = typer.Typer(
    help="Mole is a tool for automating my life.",
    no_args_is_help=True,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


@app.command()
def whack():
    """Populate tasks in Todoist"""
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

    if has_blumeops_profile():
        ensure_journal(remote)
    else:
        typer.secho("🤷 Skipping Journal Check (no 'blumeops' AWS profile found)", fg=typer.colors.YELLOW)

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
    import os
    import openai
    from .game import Game, Player

    openai.api_key = os.getenv('OPENAI_API_KEY')

    game = Game(Player())
    game.run()


@app.command()
def summary(temperature: float = 0.3, extra_prompt: str = ""):
    """Get an LLM summary of the day"""
    import openai
    import os
    openai.api_key = os.getenv('OPENAI_API_KEY')

    from .summary import get_summary
    typer.echo(get_summary(temperature=temperature, extra_prompt=extra_prompt))


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def miniflux(ctx: typer.Context):
    """Run miniflux - runs with exec, so mole will exit"""
    # TODO add upgrade logic
    # Check for executable dir
    miniflux_dir = Path.home() / 'code/3rd/miniflux/'
    if not miniflux_dir.exists():
        miniflux_dir.mkdir(parents=True)
        typer.secho(f"🐭 Created miniflux dir at {miniflux_dir}", fg=typer.colors.YELLOW)

    # Check for miniflux executable
    miniflux = miniflux_dir / 'miniflux'
    if not miniflux.exists():
        miniflux_bin = miniflux_dir / 'miniflux-darwin-arm64'
        typer.secho(f"🐭 Downloading miniflux to {miniflux_bin}", fg=typer.colors.YELLOW)
        url = "https://github.com/miniflux/v2/releases/download/2.0.45/miniflux-darwin-arm64"
        r = requests.get(url)
        miniflux_bin.write_bytes(r.content)
        miniflux_bin.chmod(0o755)
        miniflux.symlink_to(miniflux_bin)

    # Construct DATABASE_URL for postgres
    db_user = 'miniflux'
    db_pass = get_item('miniflux', 'password')
    db_host = 'localhost'
    db_port = 5432
    db_name = 'miniflux'
    # TODO fix sslmode issue
    db_url = f"postgres://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?sslmode=disable"
    os.environ['DATABASE_URL'] = db_url

    # Run miniflux with exec
    os.execv(miniflux, [str(miniflux)] + list(ctx.args))


@app.command()
def version():
    """Print the version"""
    from . import __version__
    typer.echo(f"mole version {__version__}")


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    if os.getenv('VIRTUAL_ENV') and sys.argv[0].endswith('mole'):
        typer.echo("🐭 Error: detected poetry environment AND pipx entrypoint, this will surely cause PYTHONPATH conflicts, aborting")
        sys.exit(1)
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
