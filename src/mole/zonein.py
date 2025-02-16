import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from .notebook import Logbook
from .projects import Project, ToDo


def zonein(
    project_name: Annotated[Optional[str], typer.Argument(metavar="PROJECT")] = None,
    todo_name: Annotated[Optional[str], typer.Argument(metavar="TODO")] = None,
    skip_todo: Annotated[
        bool, typer.Option("--skip-todo", "-s", help="Skip the TODO prompt")
    ] = False,
):
    """zone in to a project, setting the environment accordingly.

    If the project is already running, attach to it. Otherwise, create it.

    If a TODO is provided, set MOLE_TODO to that value. It should be in the form "project.session_name:todo_number" or just "todo_number".

    If PROJECT or TODO are not provided, they will be selected interactively using fzf. If --skip-todo is provided, TODO will not be prompted.
    """

    zellij_session = os.environ.get("ZELLIJ_SESSION_NAME", None)
    if zellij_session is not None:
        print(f"🐭 Already in zellij session {zellij_session}, doing nothing")
        print(
            "(To change projects, detach with C-o d or exit with C-q and then run mole zonein again.)"
        )
        # You can also use C-o w to use the session manager, which means zellij is CAPABLE of switching sessions, but
        # they don't expose that functionality to the CLI. See:
        # - https://github.com/zellij-org/zellij/pull/2962
        # - https://github.com/zellij-org/zellij/pull/2049
        # This is going to require more work to get right, so for now we just exit.
        return

    if project_name:
        project = Project.load(project_name)
    else:
        project = Project.from_fzf()

    todo = None
    if not todo_name and not skip_todo:
        todo = ToDo.from_fzf(project)
    elif todo_name:
        match = re.match(
            r"^((?P<session_name>[^:]+):)?(?P<todo_number>\d+)$", todo_name
        )

        if not match:
            print(
                f"🐭 Error: TODO {todo_name} is not in the form `project.session_name:todo_number`"
            )
            raise typer.Exit(1)

        if (
            match.group("session_name")
            and match.group("session_name") != project.session_name
        ):
            print(
                f"🐭 Error: TODO {todo_name} is for session {match.group('session_name')}, but project {project.name} is in session {project.session_name}"
            )
            raise typer.Exit(1)

        todo = ToDo(project, int(match.group("todo_number")))

    # Print a log message
    logbook = Logbook(project)
    if todo is None:
        preamble = "🐭 zonein"
    else:
        preamble = f"🐭 zonein to {todo.label}"
    logbook.append_log_header(preamble=preamble)

    # If the session exists, attach to it
    try:
        zellij_sessions = [
            line.strip()
            for line in subprocess.check_output(
                ["zellij", "list-sessions", "-n", "-s"], text=True
            ).splitlines()
        ]
    except subprocess.CalledProcessError:
        zellij_sessions = []

    if project.session_name in zellij_sessions:
        subprocess.call(["zellij", "attach", project.session_name])
    else:
        # The session doesn't exist and we aren't attached to anything so go ahead and create it and set the environment
        os.environ["MOLE_PROJECT"] = project.name
        if todo and todo != "None":
            os.environ["MOLE_TODO"] = todo.label
        else:
            os.environ.pop("MOLE_TODO", None)

        if project.data.cwd:
            path = Path(project.data.cwd).expanduser()
            if path.is_dir():
                os.chdir(path)
            else:
                print(f"🐭 Error: cwd {path} does not exist")
                raise typer.Exit(1)

        with tempfile.NamedTemporaryFile("w+", suffix=".kdl") as f:
            f.write(project.zellij_layout)
            f.flush()
            subprocess.call(
                ["zellij", "--session", project.session_name, "--layout", f.name]
            )

    # Print a closing log message
    logbook.append_log_footer()
