# -*- coding: utf-8 -*-
import os
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from typing import Optional

import typer
from pendulum import DateTime
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
        from .projects import Project

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
def zonein(
    task: Optional[str] = typer.Argument(None), project: Optional[str] = typer.Argument(None, envvar="MOLE_PROJECT")
):
    """Focus on a specific task, launching (or resuming) a zellij session.

    The `task` parameter itself is strictly optional, although future versions may use this to provide more context. If
    no task is specified, the current project name is used. If no project is specified, a list of projects is provided
    to choose from. If you want to start a new project, use `mole projects create` instead.

    If MOLE_PROJECT was not set but the task was and the task is a project name, that project will be loaded in the
    MOLE_PROJECT environment variable for the subprocess shell.
    """
    from .projects import Project, project_names

    projects = project_names()

    # First, set task and project_obj based on the arguments and environment
    # TODO this dance is because we want to support tasks within projects, so lets actually do that
    project_obj: Optional[Project] = None
    if project is None:
        if task is None:
            mole_cmd = "mole"
            if sys.argv[0].endswith("__main__.py"):
                mole_cmd = f"{sys.executable} -m mole"
            command = ["fzf", "--prompt", "project: "]
            command += ["--preview", mole_cmd + " projects show --color=always {}"]
            # TODO change the above to use sys.argv and sys.executable to cover all the bases
            choices = "\n".join(projects)
            choice = subprocess.check_output(command, input=choices.encode()).decode().strip()
            project_obj = Project.load(choice)
        elif task in projects:
            project_obj = Project.load(task)
    else:
        if project not in projects:
            typer.echo("🐭 Error: project not found")
            raise typer.Exit(1)
        project_obj = Project.load(project)
        if task is None:
            task = project
    # Now, task is definitely set, and project_obj is set if we know about this project

    # If we know about this session as a project, open it like a project
    if project_obj is not None:
        os.environ["MOLE_PROJECT"] = project_obj.name
        # Try and resume, if possible. (We can't use zellij attach --create because it won't let us apply a layout)
        if (
            project_obj.session_name
            in subprocess.run(["zellij", "ls", "--short"], capture_output=True).stdout.decode().splitlines()
        ):
            os.execvp("zellij", ["zellij", "attach", project_obj.session_name])
            # If I start seeing command prompts again, re-enable --force-run-commands like so:
            # os.execvp("zellij", ["zellij", "attach", project_obj.session_name, "--force-run-commands"])
            # TODO delete this when its clear its not happening without serialization

        # Make a layout file with tempfile.
        # TODO use zellij's layout directory system and couple it with project metadata and let projects specify
        # per-project layouts automatically. Zellij layout is REALLY POWERFUL, especially with custom plugins, it can be
        # so much more than just a terminal multiplexer. What follows is just a mere taste of what's possible.
        with tempfile.NamedTemporaryFile(suffix="layout.kdl") as f:
            f.write(
                textwrap.dedent(
                    f"""\
                    // auto-generated layout file using mole zonenin command
                    // generated by: {__file__}

                    session_serialization false
                    layout {{
                        pane size=1 borderless=true {{
                            plugin location="zellij:tab-bar"
                        }}
                        pane split_direction="vertical" {{
                            pane size="60%"
                            pane {{
                                command "mole"
                                args "log"
                            }}
                        }}
                        pane size=2 borderless=true {{
                            plugin location="zellij:status-bar"
                        }}
                    }}
                    """
                ).encode()
            )
            f.flush()
            os.execvp("zellij", ["zellij", "--session", project_obj.session_name, "--layout", f.name])

    # Finally, if all else fails, just launch zellij with a task name if possible
    if task:
        os.execvp("zellij", ["zellij", "--session", task])
    os.execvp("zellij", ["zellij"])


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
