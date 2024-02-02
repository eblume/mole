import os
from typing import Optional

import typer
from pendulum import DateTime
from typing_extensions import Annotated

from mole.notebook import Logbook

from .projects import ProjectOption, ToDoOption
from .typer_command import forward

app = typer.Typer(help="Manipulate tasks related to projects via nb-cli commands")


@app.command("list")
def list_tasks(
    target: Annotated[Optional[str], typer.Argument()] = None,
    project: ProjectOption = None,
    todo: ToDoOption = None,
    closed: Annotated[bool, typer.Option("--closed", "-c", is_flag=True, help="Show closed tasks")] = False,
    include_all: Annotated[bool, typer.Option("--all", "-a", is_flag=True, help="Show all tasks")] = False,
):
    """List tasks for the project or from the home notebook if no project is given.

    If 'target' is specified, then --project and --todo are ignored and the target is used directly in the nb command.

    Unlike the default nb behavior, only open tasks are shown by default. Use --closed to show closed tasks, and --all to show all tasks.

    If --todo is specified, then only tasks in the given todo are shown.
    """
    cmd = ["nb", "tasks"]

    if target is not None:
        cmd.append(target)
    elif todo is not None:
        cmd.append(todo.label)
    elif project is not None:
        cmd.append(f"{project.session_name}:")

    if closed and include_all:
        raise typer.BadParameter("Cannot use both --closed and --all")
    elif closed:
        cmd.append("closed")
    elif not include_all:
        cmd.append("open")

    os.execvp("nb", cmd)


@app.command("do")
def do_task(target: str, task: Annotated[Optional[str], typer.Argument()] = None, project: ProjectOption = None):
    """Close ('do') the given task. eg. 'do myproj:2 2'

    If 'target' is specified, then it is used verbatim in the underlying `nb do` command, ignoring --project and
    MOLE_PROJECT. Otherwise it will be inferred from either the project (if specified) or from today's daily log entry
    (otherwise).

    Nothing is done to ensure that the given task is open or that the log file for this day exists, and in such cases
    the underlying `nb` system will produce errors.
    """
    cmd = ["nb", "task", "do"]
    if task is None:
        task = target  # target is actually the task in this case, first argument cant be optional in typer
        logbook = Logbook(project)
        target = logbook.get_or_create_log(DateTime.now())
    cmd.extend([target, task])
    os.execvp("nb", cmd)


@app.command("undo")
def undo_task(target: str, task: Annotated[Optional[str], typer.Argument()] = None, project: ProjectOption = None):
    """Exactly the inverse of 'do'. eg. 'undo myproj:2 2'"""
    cmd = ["nb", "task", "undo"]
    if task is None:
        task = target
        logbook = Logbook(project)
        target = logbook.get_or_create_log(DateTime.now())
    cmd.extend([target, task])
    os.execvp("nb", cmd)


@app.command("add")
def add_task(
    entry: list[str],
    target: Annotated[Optional[str], typer.Option(help="Target notebook entry, eg. 'myproj:2'.")] = None,
    project: ProjectOption = None,
):
    """Create a new task with the given entry text.

    As with 'list', if 'target' is specified it will override the project specified by --project or MOLE_PROJECT.

    If no target is specified, the current day's log is used. If the log does not exist, it is created.
    """
    cmd = ["nb", "edit"]
    if target is None:
        logbook = Logbook(project)
        todays_log = logbook.get_or_create_log(DateTime.now())
        cmd.append(todays_log)
    task_text = f"- [ ] {' '.join(entry)}"
    cmd = ["nb", "edit", target, "--content", task_text]
    os.execvp("nb", cmd)


@app.command("todo")
def add_todo(
    title: list[str],
    project: ProjectOption = None,
):
    """Create a new ToDo with the given title.

    If a project is specified, the todo is created in the project's todo notebook. Otherwise, the todo is created in the home notebook.
    """
    cmd = ["nb", "todo", "add"]
    if project is not None:
        cmd.append(f"{project.session_name}:")
    cmd.extend(["--title", " ".join(title)])
    os.execvp("nb", cmd)


@app.callback(invoke_without_command=True)
def tasks(
    ctx: typer.Context,
    target: Optional[str] = None,
    project: ProjectOption = None,
    todo: ToDoOption = None,
    closed: Annotated[bool, typer.Option("--closed", "-c", is_flag=True, help="Show closed tasks")] = False,
    include_all: Annotated[bool, typer.Option("--all", "-a", is_flag=True, help="Show all tasks")] = False,
):
    """Manipulate tasks related to projects via nb-cli commands"""
    # TODO: `mole tasks mole:` should show all tasks for the mole project but instead errors out
    # Workaround is to use the full form `mole tasks list mole:`
    if ctx.invoked_subcommand is None:
        forward(app, list_tasks, target=target, project=project, todo=todo, closed=closed, include_all=include_all)
