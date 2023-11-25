# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from typerassistant import TyperAssistant

from .projects import app as project_app
from .secrets import get_secret


@dataclass(init=False)
class MoleCLI(typer.Typer):
    assistant: TyperAssistant | None = None


app = MoleCLI(
    name="mole",
    help="Mole is a tool for automating my life.",
    no_args_is_help=True,
)


@app.command()
def version():
    """Print the version"""
    from . import __version__

    typer.echo(f"mole version {__version__}")


@app.command()
def health():
    """Run health checks for this mole instance"""
    from .health import health_checks

    def _make_table():
        table = Table(title="Health Checks", show_header=True, header_style="bold magenta")
        table.add_column("")
        table.add_column("Check")
        table.add_column("Status")

        count = 0
        success = 0
        for check in health_checks():
            count += 1
            if check.status.value == "success":
                success += 1
            table.add_row(check.status.emoji, f"[{check.status.color}]{check.name}[/]", check.message)

        table.add_section()
        table.add_row("", "[bold]Total[/]", f"{success}/{count} checks passed")

        return table

    console = Console()
    console.print(_make_table())


@app.command()
def whack():
    """Whack the mole. A long-lived watcher process.

    This entrypoint spawns a long-lived watcher process that will react to certain events. It is intended to be run with
    OP_SERVICE_ACCOUNT_TOKEN set for secret access, or else it will block on user acceptance for access (which is fine.)
    """
    # TODO unwrap this, I just can't test it right now
    from .whack import whack

    whack()


@app.command()
def log(
    entry_text: Optional[str] = typer.Argument(None), subtitle: Optional[str] = typer.Option(None, "--subtitle", "-s")
):
    """Add an entry to the daily log."""
    from .notebook import add_log

    # Check if stdin has data
    if not sys.stdin.isatty():
        if entry_text:
            typer.echo("🐭 Error: stdin and entry_text are mutually exclusive")
            raise typer.Exit(1)

        entry_text = "".join(sys.stdin.readlines())

    add_log(entry_text, subtitle)


app.add_typer(project_app, name="projects")


@app.command()
def zonein(task: str):
    """Zone in on a specific task.

    For now, simply opens a zellij session named after the task.
    """
    # For the session name, we want to strip out all non-alphanumeric characters and replace with dashes
    session_name = "".join([c if c.isalnum() else "-" for c in task.lower()])
    short = textwrap.shorten(session_name, width=20, placeholder="...")

    # Find all existing project files in nb
    projects = map(
        Path, subprocess.check_output(["nb", "ls", "--type=project.md", "--paths", "--no-id"]).decode().splitlines()
    )
    # Map the session-format of the project name to the project file in nb
    # (eg. "/Users/erichdblume/.nb/home/my_project.project.md" -> {"my-project": "my_project.project.md"})
    # Collisions are entirely unhandled and will surely cause problems. (#TODO)
    names = {
        "".join([c if c.isalnum() else "-" for c in project.stem.split(".")[0].lower()]): project.name
        for project in projects
    }

    # If we know about this session as a project, open it like a project
    if session_name in names:
        project = names[session_name]

        # Make a layout file with tempfile
        # TODO won't this leak tempfiles? I don't really care, they are super small, but we should figure it out.
        with tempfile.NamedTemporaryFile(suffix="layout.kdl") as f:
            # TODO in the future we can use zellij's plugin "strider" along with project metadata to open an IDE-like
            # interface in a project directory.
            f.write(
                textwrap.dedent(
                    f"""\
                    // auto-generated layout file using mole zonenin command
                    // generated by: {__file__}

                    layout {{
                        pane split_direction="vertical" {{
                            pane size="60%"
                            pane {{
                                command "nb"
                                args "edit" "{project}"
                            }}
                        }}
                    }}
                    """
                ).encode()
            )
            f.flush()
            os.execvp("zellij", ["zellij", "--session", short, "--layout", f.name])

    os.execvp("zellij", ["zellij", "--session", short])


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def svcrun(ctx: typer.Context):
    """Execute a command by wrapping it with a service account token. Any arguments are processed as a command."""
    # TODO figure out how to get the --help to show COMMAND... instead of just [OPTIONS]
    command = ctx.args
    if not command:
        typer.echo("🐭 Error: no command specified")
        raise typer.Exit(1)
    typer.echo(
        "Loading service account token. This may prompt via 1password's GUI once and then the token will be cached."
    )
    typer.echo("(If this hangs, you need to run again from a terminal with a GUI.)")
    token = get_secret("zukqtgtw5xt66k3z3il4hw366e", "credential", vault="blumeops")
    typer.echo("Service account token loaded, the command will now run without interruption from 1password.")

    env = os.environ.copy()
    env["OP_SERVICE_ACCOUNT_TOKEN"] = token

    try:
        subprocess.run(command, env=env, check=True, capture_output=False)
    except Exception as e:
        typer.echo(f"🐭 Error: {e}")
        raise typer.Exit(1)


@app.command()
def task(task: str):
    """Add a task to the todo list."""
    from .todoist import create_task

    typer.echo(create_task(task))
