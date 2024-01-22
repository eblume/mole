# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from typing import Optional

import openai
import typer
from rich.console import Console
from rich.table import Table
from typerassistant import TyperAssistant

from .notebook import Logbook
from .projects import AssistantData, Project, ProjectOption, ToDo
from .projects import app as project_app
from .secrets import get_secret
from .tasks import app as tasks_app
from .whack import whack
from .zonein import zonein

app = typer.Typer(
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
def log(
    entry_text: Optional[str] = typer.Argument(None),
    subtitle: Optional[str] = typer.Option(None, "--subtitle", "-s"),
    project: Optional[str] = typer.Argument(None, envvar="MOLE_PROJECT"),
    todo: Optional[str] = typer.Argument(None, envvar="MOLE_TODO"),
):
    """Add an entry to the daily log.

    If project is specified, the log will be created in that projects' notebook. (A notebook will be created if one did not exist.)

    If todo is further specified beyond project, then the log will instead be created as a subheading (h2) of that todo in the corresponding project. This overrides the project log destination.
    """
    if project is None:
        logbook = Logbook(project=None)
    elif todo is None:
        logbook = Logbook(project=Project.load(project))
    else:
        logbook = Logbook(project=Project.load(project), todo=ToDo.from_label(todo))

    # Check if stdin has data
    if not sys.stdin.isatty():
        if entry_text:
            typer.echo("🐭 Error: stdin and entry_text are mutually exclusive")
            raise typer.Exit(1)
        entry_text = "".join(sys.stdin.readlines())
        logbook.append_log(entry_text, preamble=subtitle)
    else:
        if entry_text:
            logbook.append_log(entry_text, preamble=subtitle or "")  # None signals to print no header
        else:
            if todo is not None and subtitle is None:
                # Special case for todos, where we always want to print a header as they are subheadings
                subtitle = ""
            logbook.edit_log(preamble=subtitle)


app.add_typer(project_app, name="projects")
app.add_typer(tasks_app, name="tasks")
app.command()(zonein)
app.command()(whack)


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

    # Shouldn't this just be:
    # os.execvpe(command[0], command, env=env)

    try:
        subprocess.run(command, env=env, check=True, capture_output=False)
    except Exception as e:
        typer.echo(f"🐭 Error: {e}")
        raise typer.Exit(1)


@app.command()
def todoist(task: str):
    """Add a task to the todo list in todoist. Has no relation to 'tasks' command."""
    from .todoist import create_task

    typer.echo(create_task(task))


@app.command(context_settings={"obj": {"omit_from_assistant": True}})
def ask(
    query: str,
    project: ProjectOption = None,
    replace_assistant: bool = False,
    use_commands: bool = False,
    confirm_commands: bool = True,
):
    """Ask a question of the OpenAI Assistant API, optionally delegating mole commands for you.

    If a project is specified, the assistant will be scoped to that project. The project.data.assistant object will be
    examined to construct the assistant, thread, and run objects for the conversation. If not specified, a generalized assistant will be created.

    If replace_assistant is True, the assistant will be replaced before asking the question, remotely in the OpenAI Assistant API.

    If use_commands is True, the assistant will be asked to execute the commands it generates. If False, any commands available to the model will be suppressed for this question.

    If confirm_commands is True, the assistant will ask for confirmation before executing the commands it generates.
    """
    client = openai.OpenAI(api_key=get_secret("OpenAI", "credential", vault="blumeops"))

    # Build or retrieve an assistant and thread
    if project and project.data.assistant:
        if project.data.assistant.id and not replace_assistant:
            assistant = TyperAssistant.from_id_with_app(project.data.assistant.id, app, client=client)
        else:
            # TODO support project.data.assistant.name in TyperAssistant
            assistant = TyperAssistant(app, client=client, replace=replace_assistant)
        thread = assistant.thread(project.data.assistant.thread_id)
    else:
        assistant = TyperAssistant(app, client=client, replace=replace_assistant)
        thread = assistant.thread()

    # Ask the question on the thread (this is a 'run')
    response = assistant.ask(query, thread=thread, use_commands=use_commands, confirm_commands=confirm_commands)
    print(response)

    # Update the project assistant data, if relevant
    if project:
        # TODO figure out what to do about overwriting the assistant name, etc.
        project.data.assistant = AssistantData(id=assistant.assistant.id, thread_id=thread.id)
        project.write()
