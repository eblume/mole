# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer
from pendulum import DateTime
from rich.console import Console
from rich.table import Table
from typerassistant import TyperAssistant
from typing_extensions import Annotated

from .projects import Project, ProjectOption
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
    entry_text: Optional[str] = typer.Argument(None),
    subtitle: Optional[str] = typer.Option(None, "--subtitle", "-s"),
    project: Optional[str] = typer.Argument(None, envvar="MOLE_PROJECT"),
):
    """Add an entry to the daily log."""
    from .notebook import add_log

    # Check if stdin has data
    if not sys.stdin.isatty():
        if entry_text:
            typer.echo("🐭 Error: stdin and entry_text are mutually exclusive")
            raise typer.Exit(1)

        entry_text = "".join(sys.stdin.readlines())

    # Pre-sync... not going to fix all the problems, but should help
    subprocess.check_output(["nb", "sync"])

    if not project:
        add_log(entry_text, subtitle)
    else:
        # TODO unify notebooks and project logs, see mole.project.md around 4 Dec 2023
        project_obj = Project.load(project)

        # Some of the following logic is copied from add_log, but this all needs to be refactored anyway
        when = DateTime.now()
        content = f"## {when.strftime('%A, %B %d, %Y (%H:%M)')} {subtitle or ''}\n\n{entry_text or ''}"
        subprocess.check_output(["nb", "edit", str(project_obj.nb_logfile_id), "--content", content])
        if not entry_text:
            # (see comment in add_log)
            subprocess.run(["nb", "open", str(project_obj.nb_logfile_id)])

    # Post-sync. Required.
    subprocess.check_output(["nb", "sync"])


app.add_typer(project_app, name="projects")


@app.command()
def zonein(project_name: Annotated[Optional[list[str]], typer.Argument(metavar="PROJECT")] = None):
    """zonein to a project, setting the environment accordingly.

    The project name is, as a convenience, joined with spaces, or you can specify it in one "quoted string". If no project name is given, you will be prompted by fzf to choose a project.
    """
    if project_name:
        project = Project.load(" ".join(project_name))
    else:
        project = Project.from_fzf()

    os.environ["MOLE_PROJECT"] = project.name

    if project.data.cwd:
        path = Path(project.data.cwd).expanduser()
        if path.is_dir():
            os.chdir(path)
        else:
            print(f"🐭 Error: cwd {path} does not exist")
            raise typer.Exit(1)

    try:
        subprocess.run(["zellij", "attach", project.session_name], check=True)
    except subprocess.CalledProcessError:
        # No session exists, so create one
        with tempfile.NamedTemporaryFile("w+", suffix=".kdl") as f:
            f.write(project.zellij_layout)
            f.flush()
            os.execvp("zellij", ["zellij", "--session", project.session_name, "--layout", f.name])
            # TODO does this leak temporary files?


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


@app.command(context_settings={"allow_extra_args": True, "ignore_unknown_options": True})
def tasks(ctx: typer.Context, project: ProjectOption = None):
    """Shortcut for `nb tasks <project_id> [COMMAND]...`

    # To print all open tasks for the 'foo' project
    MOLE_PROJECT="foo" mole tasks open

    # To close the 4th task for the 'foo' project
    MOLE_PROJECT="foo" mole tasks close 4

    # To list all tasks
    mole tasks
    """
    cmd = ["nb", "tasks"]
    if project is not None:
        cmd.append(str(project.nb_logfile_id))

    if ctx.args:
        cmd.extend(ctx.args)

    os.execvp("nb", cmd)


@app.command()
def task(task: str):
    """Add a task to the todo list in todoist. Has no relation to 'tasks' command."""
    # TODO rename this, it has nothing to do with tasks now! (See also voicememo.py prompt!)
    from .todoist import create_task

    typer.echo(create_task(task))
