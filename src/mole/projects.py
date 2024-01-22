from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

import pendulum
import typer
import yaml
from pydantic import BaseModel, ConfigDict
from rich import print
from typing_extensions import Annotated

from .zellij import CommandPane, Layout, Pane, PluginPane

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper, Loader


# Note that these names will be compared against Project.session_name.lower()
FORBIDDEN_NAMES = ["none", "home"]


class BatColorChoice(str, Enum):
    always = "always"
    never = "never"
    auto = "auto"


ProjectRef = Union[int, str, Path]


class AssistantData(BaseModel):
    """Data for the TyperAssistant for this project"""

    id: Optional[str] = None
    name: Optional[str] = None
    thread_id: Optional[str] = None


class ProjectData(BaseModel):
    model_config = ConfigDict(extra="allow")

    created: Optional[datetime] = None
    description: Optional[str] = None
    log_dir: Optional[str] = None
    cwd: Optional[str] = None
    poetry: Optional[bool] = None
    assistant: Optional[AssistantData] = None


@dataclass(frozen=True)
class Project:
    """A project is a combined Markdown and YAML serialized file.

    The first line is always a markdown title, which parses in YAML as a comment. This field is the 'name' of the project, which should correspond to the file name, but this is not enforced.

    The rest of the file is YAML, which is parsed into a ProjectData object.
    """

    nb_id: int
    name: str
    data: ProjectData

    @classmethod
    def load(cls, ref: ProjectRef) -> Project:
        """Load a project from a file, id, or name.

        It is slightly more efficient to load by id (int), since this avoids a call to nb, but this is not required.

        If providing a path, it can be relative, absolute, or a bare filename. See `nb ls` and `nb search` for more details on the search methods used.
        """
        if isinstance(ref, int):
            nb_id = ref
        else:
            try:
                if isinstance(ref, Path):
                    output = (
                        subprocess.check_output(["nb", "ls", "home:", "--no-color", "--filenames", str(ref)])
                        .decode()
                        .strip()
                    )
                else:
                    output = (
                        subprocess.check_output(
                            ["nb", "search", "home:", "--no-color", "-l", "--type", "project.yaml", f"^# {ref}$"]
                        )
                        .decode()
                        .strip()
                    )
            except subprocess.CalledProcessError as e:
                if e.returncode == 1:
                    raise ValueError(f"Could not find project matching {ref}")
                raise
            lines = output.splitlines()
            if len(lines) != 1:
                raise RuntimeError(f"Found {len(lines)} projects matching {ref}")
            match = re.match(r"^\[(\d+)\] .+$", lines[0])
            if not match:
                raise RuntimeError(f"Could not parse output: {output}")
            nb_id = int(match.group(1))

        record = subprocess.check_output(["nb", "show", f"home:{nb_id}", "--no-color", "--print"]).decode()
        match = re.match(r"^# ([^\n]+)\n", record)
        if not match:
            raise RuntimeError(f"Could not parse output: {record}")
        name = match.group(1)
        data = yaml.load(record, Loader=Loader)

        return cls(nb_id, name, data=ProjectData(**data))

    @classmethod
    def from_fzf(cls) -> Project:
        """Prompt the user to choose a project using fzf."""
        mole_cmd = "mole"
        if sys.argv[0].endswith("__main__.py"):
            mole_cmd = f"{sys.executable} -m {mole_cmd}"
        command = [
            "fzf",
            "--prompt",
            "Choose a project: ",
            "--preview",
            f"{mole_cmd} projects show --color=always {{}}",
        ]
        choices = "\n".join(sorted(project_names(), reverse=True))
        choice = subprocess.check_output(command, input=choices.encode()).decode().strip()
        return cls.load(choice)

    @classmethod
    def create(cls, name: str) -> Project:
        """Create a new project"""
        if not re.match(r"^[a-zA-Z0-9_\- ]+$", name):
            raise ValueError(f"Project name {name} is invalid")

        if name in FORBIDDEN_NAMES:
            raise ValueError(f"Project name {name} is forbidden")

        if name in project_names():
            raise ValueError(f"Project {name} already exists")

        # First we create a 'dummy' project to get the YAML representation
        now = datetime.fromisoformat(pendulum.now().isoformat())  # TODO pydantic doesn't like pendulum datetimes
        data = ProjectData(created=now)

        dummy = cls(nb_id=-1, name=name, data=data)
        dummy.write()
        # Then, load that project properly
        return Project.load(name)

    @property
    def session_name(self) -> str:
        """Returns a session name for zellij"""
        # Convert to lowercase, spaces to underscores, and strip non-alphanumeric characters
        no_spaces = self.name.lower().replace(" ", "_")
        return "".join([c if c.isalnum() else "-" for c in no_spaces])

    @property
    def file(self) -> Path:
        """Return the full path to the project file."""
        if self.nb_id == -1:
            raise RuntimeError("Cannot get file for dummy project")
        path = Path(
            subprocess.check_output(["nb", "ls", f"home:{self.nb_id}", "--no-color", "--paths", "--no-id"])
            .decode()
            .strip()
        )
        assert path.exists()
        return path

    @property
    def zellij_layout(self) -> str:
        """Return the zellij layout for this project."""
        shell = os.environ.get("SHELL", "bash")
        task_command = [shell, "-c", "mole tasks; exec $SHELL -i"]
        layout = Layout(config={"session_serialization": False})
        if self.data.poetry:
            main_pane = CommandPane(command=["poetry", "shell"], props=CommandPane.Props(size="60%", name="main"))
        else:
            main_pane = Pane(props=Pane.Props(size="60%", name="main"))
        layout.panes += [
            PluginPane(
                location="zellij:tab-bar",
                props=PluginPane.Props(size=1, borderless=True),
            ),
            Pane(
                panes=[
                    main_pane,
                    Pane(
                        panes=[
                            CommandPane(
                                command=["mole", "log"],
                                props=CommandPane.Props(name="log", focus=True),
                            ),
                            CommandPane(
                                command=task_command,
                                props=CommandPane.Props(name="tasks"),
                            ),
                        ],
                        props=Pane.Props(stacked=True),
                    ),
                ],
                props=Pane.Props(split_direction="vertical"),
            ),
            PluginPane(
                location="zellij:status-bar",
                props=PluginPane.Props(size=2, borderless=True),
            ),
        ]

        return layout.dump()

    def dump(self, title: bool = True) -> str:
        """Dump the project to a Markdown+YAML string, as expected by load()

        if title is True (the default), include the title in the markdown. You'll need to turn this off if you're using
        nb to create a new file, since it will add the title for you.
        """
        data = self.data.model_dump(exclude_none=True)
        preamble = f"# {self.name}\n" if title else ""
        return preamble + yaml.dump(data, Dumper=Dumper, explicit_start=True, explicit_end=True)

    def write(self):
        """Write the project to disk. This is not thread-safe."""
        # Race condition: if the file is modified between the read and the write, the changes will be lost, etc.
        # nb sync manages collision at the git level, at least, so network effects are usually not a problem.
        if self.nb_id == -1:
            # Sentinel: this is a dummy project, so we need to create it
            self.nb_add_file(self.name, "project.yaml", self.dump(title=False))
        else:
            subprocess.check_output(
                ["nb", "edit", f"home:{self.nb_id}", "--overwrite", "--content", self.dump(title=True)]
            )
        subprocess.check_output(["nb", "sync"])

    def nb_add_file(self, name: str, filetype: str, content: Optional[str] = None) -> int:
        """Add a file to the notebook"""
        command = ["nb", "add", "home:", "--no-color", f"--type={filetype}", "--title", name]
        if content:
            command.extend(["--content", content])
        output = subprocess.check_output(command).decode()
        match = re.match(r"Added: \[(\d+)\]", output)
        if not match:
            raise RuntimeError(f"Could not parse output: {output}")
        return int(match.group(1))

    def list_todos(self) -> List[str]:
        """List the labels of all the open todos in this project."""
        command = ["nb", "todos", "--no-color", f"{self.session_name}:", "open"]
        try:
            output = subprocess.check_output(command).decode()
        except subprocess.CalledProcessError as e:
            if e.returncode == 1:
                return []
            raise
        return [line.strip() for line in output.splitlines()]


@dataclass(frozen=True)
class ToDo:
    project: Project
    todo: int

    @classmethod
    def from_fzf(cls, project: Project) -> Optional[ToDo]:
        """Prompt the user to choose a TODO using fzf."""
        command = [
            "fzf",
            "--prompt",
            "Choose a TODO: ",
            "--preview",
            "nb show --color=always {}",
        ]
        choices = "None\n" + "\n".join(sorted(project.list_todos(), reverse=True))
        choice = subprocess.check_output(command, input=choices.encode()).decode().strip()
        match = re.match(r"^\[(\w+):(\d+)\] .+$", choice)
        if not match:
            return None
        if match.group(1) != project.session_name:
            raise RuntimeError(f"TODO {choice} is not in project {project.name}")
        return cls(project, int(match.group(2)))

    @classmethod
    def from_label(cls, label: str) -> ToDo:
        """Parse a label into a ToDo"""
        match = re.match(r"^((\w+):)?(\d+)$", label)
        if not match:
            raise ValueError(f"Could not parse label {label}")
        project_name = match.group(2)
        todo = int(match.group(3))
        if project_name:
            project = Project.load(project_name)
        elif os.environ.get("MOLE_PROJECT"):
            project = Project.load(os.environ["MOLE_PROJECT"])
            project_name = project.session_name
        else:
            # While although we COULD assume a "home:" notebook in this case, this would mean we need to support ToDos
            # that do not belong to a project, and at the moment we want to ensure this tight coupling of ToDos and
            # Projects, so we raise an error instead.
            raise ValueError(f"Could not parse label {label}: no project specified")
        return cls(project, todo)

    @property
    def label(self) -> str:
        return f"{self.project.session_name}:{self.todo}"


ProjectOption = Annotated[
    Optional[Project], typer.Option("--project", "-p", envvar="MOLE_PROJECT", parser=Project.load)
]
ToDoOption = Annotated[Optional[ToDo], typer.Option("--todo", "-t", envvar="MOLE_TODO", parser=ToDo.from_label)]


def project_ids() -> set[int]:
    """Return a set of project ids by querying nb."""
    output = subprocess.check_output(["nb", "ls", "home:", "--no-color", "--type=project.yaml"]).decode()
    if not output:
        raise RuntimeError("Could not get projects, check `nb status`, there may be a git index issue.")
    if "0 project.yaml items" in output:
        return set()
    return {int(match.group(1)) for match in re.finditer(r"^\[(\d+)\] .+$", output, re.MULTILINE)}


def project_names() -> set[str]:
    """Return a set of project names by querying nb."""
    output = subprocess.check_output(
        ["nb", "ls", "home:", "--no-color", "--type=project.yaml", "--excerpt", "1"]
    ).decode()
    # The output is a series of 4-line groups, like this:
    # [1] Project file
    # ----------------
    # # Project Name
    # <empty line>
    if not output:
        raise RuntimeError("Could not get projects, check `nb status`, there may be a git index issue.")
    if "0 project.yaml items" in output:
        return set()
    found = set()
    for match in re.finditer(r"^\[(\d+)\] .+\n-+\n# (.+)\n$", output, re.MULTILINE):
        if match.group(2) in found:
            raise RuntimeError(f"Duplicate project name: {match.group(2)} (one has id {match.group(1)})")
        found.add(match.group(2))
    return found


## Typer app


app = typer.Typer(help="Manage projects", no_args_is_help=True)


@app.command()
def list():
    """List all projects"""
    for project_name in sorted(project_names(), reverse=True):
        print(project_name)


@app.command()
def create(name: str):
    """Create a new project"""
    try:
        Project.create(name)
    except ValueError as e:
        print(e)
        raise typer.Exit(1)


@app.command()
def show(name: str, color: BatColorChoice = BatColorChoice.auto):
    """Show a project using bat.

    This will pretty-print the project when done 'bare', but if you pipe it in to another program (like `yq`), it will
    do the right thing.
    """
    project = Project.load(name)
    # NB has a 'show' command this was intended for, but perplexingly it doesn't auto-detect tty and instead relies on a
    # --print/-p flag to print the file contents. So we just use bat directly, which does all this for us.
    os.execvp("bat", ["bat", f"--color={color.value}", project.file])


@app.command()
def edit(name: str):
    """Edit a project"""
    project = Project.load(name)
    subprocess.run(["nb", "edit", f"home:{project.file}"])
    subprocess.run(["nb", "sync"])
