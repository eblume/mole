from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

import pendulum
import typer
import yaml
from pydantic import BaseModel
from rich import print
from rich.panel import Panel
from rich.prompt import Confirm

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper, Loader


class BatColorChoice(str, Enum):
    always = "always"
    never = "never"
    auto = "auto"


app = typer.Typer(help="Manage projects", no_args_is_help=True)


@app.command()
def list():
    """List all projects"""
    for project_name in sorted(get_projects().keys(), reverse=True):
        print(project_name)


@app.command()
def create(name: str):
    """Create a new project"""
    projects = get_projects()
    if name in projects:
        print(f"Project {name} already exists")
        raise typer.Exit(1)

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
    project = Project.by_name(name)
    assert project.file is not None
    # NB has a 'show' command this was intended for, but perplexingly it doesn't auto-detect tty and instead relies on a
    # --print/-p flag to print the file contents. So we just use bat directly, which does all this for us.
    os.execvp("bat", ["bat", f"--color={color.value}", project.file])


@app.command()
def edit(name: str):
    """Edit a project"""
    project = Project.by_name(name)
    assert project.file is not None
    subprocess.run(["nb", "edit", project.file])
    subprocess.run(["nb", "sync", "--no-color"])


@app.command()
def shell(name: Optional[str] = typer.Argument(default=None)):
    """Open a shell with MOLE_PROJECT set to the given project.

    If no project is given, fzf will prompt you for one. If the named project does not exist, you will be prompted to
    confirm creating it.

    The shell is opened with execvp, so it will replace this mole process.
    """
    projects = get_projects()
    if not name:
        name = (
            subprocess.check_output(["fzf"], input="\n".join(sorted(projects.keys(), reverse=True)).encode())
            .decode()
            .strip()
        )

    if name not in projects:
        if not Confirm.ask(f"Project {name} does not exist. Create it?"):
            print("Quitting without creating project")
            return
        project = Project.create(name)
    else:
        project = projects[name]

    os.environ["MOLE_PROJECT"] = project.name
    print(
        Panel.fit(
            f'env[MOLE_PROJECT]="{project.name}"',
            title=f"executing \"exec {os.environ['SHELL']}\" with:",
            border_style="red dim",
        )
    )
    # TODO is this the best way to re-exec with a new environment?
    os.execvp(os.environ["SHELL"], [os.environ["SHELL"]])


class ProjectData(BaseModel):
    created: datetime
    description: Optional[str] = None


@dataclass
class Project:
    """A project is a combined Markdown and YAML serialized file.

    The first line is always a markdown title, which parses in YAML as a comment. This field is the 'name' of the project, which should correspond to the file name, but this is not enforced.

    The rest of the file is YAML, which is parsed into a ProjectData object.
    """

    name: str
    data: ProjectData
    file: Optional[Path] = field(init=False, default=None)

    @classmethod
    def by_file(cls, file: Path) -> Project:
        """Load a project from a file"""
        text = file.read_text()
        # The first line should be a markdown title, from which we get the name.
        # (Markdown titles are of the form "# Title" and so parse as comments in YAML)
        match = re.match(r"^# ([^\n]+)\n", text)
        if match:
            name = match.group(1)
        else:  # Fallback to the filename, but strip the ".project.yaml" suffix
            name = file.name[: -1 * len(".project.yaml")]
        data = yaml.load(text, Loader=Loader)
        proj = cls(name, data=ProjectData(**data))
        proj.file = file
        return proj

    @classmethod
    def by_name(cls, name: str) -> Project:
        projects = get_projects()
        project = projects.get(name)
        if project is None:
            print(f"Project {name} does not exist")
            raise typer.Exit(1)
        return project

    @classmethod
    def create(cls, name: str) -> Project:
        """Create a new project"""
        if not re.match(r"^[a-zA-Z0-9_\- ]+$", name):
            raise ValueError(f"Project name {name} is invalid")

        if name in get_projects():
            raise ValueError(f"Project {name} already exists")

        # First we create a 'dummy' project to get the YAML representation
        now = datetime.fromisoformat(pendulum.now().isoformat())  # TODO pydantic doesn't like pendulum datetimes
        data = ProjectData(created=now)

        dummy = cls(name=name, data=data)
        dummy.write()
        # Then, load that project properly
        assert dummy.file is not None
        return Project.by_file(dummy.file)

    @property
    def session_name(self) -> str:
        """Returns a session name for zellij"""
        # Convert to lowercase, spaces to underscores, and strip non-alphanumeric characters
        no_spaces = self.name.lower().replace(" ", "_")
        return "".join([c if c.isalnum() else "-" for c in no_spaces])

    def dump(self, title: bool = True) -> str:
        """Dump the project to a Markdown+YAML string, as expected by load()

        if title is True (the default), include the title in the markdown. You'll need to turn this off if you're using
        nb to create a new file, since it will add the title for you.
        """
        data = self.data.model_dump()
        preamble = f"# {self.name}\n" if title else ""
        return preamble + yaml.dump(data, Dumper=Dumper, explicit_start=True, explicit_end=True)

    def write(self):
        """Write the project to disk. This is not thread-safe."""
        # Race condition: if the file is modified between the read and the write, the changes will be lost, etc.
        if self.file:
            self.file.write_text(self.dump())
        else:
            self.file = self.nb_add_file(self.name, "project.yaml", self.dump(title=False))
        subprocess.check_output(["nb", "sync", "--no-color"])

    def nb_add_file(self, name: str, filetype: str, content: Optional[str] = None) -> Path:
        """Add a file to the notebook"""
        if content:
            output = subprocess.check_output(
                ["nb", "add", "--no-color", f"--type={filetype}", "--title", name], input=content.encode()
            ).decode()
        else:
            output = subprocess.check_output(
                ["nb", "add", "--no-color", f"--type={filetype}", "--title", name]
            ).decode()
        # Example:
        # Added: [123] foo.project.yaml "foo"
        # We want the 123
        match = re.match(r"Added: \[(\d+)\]", output)
        if not match:
            raise RuntimeError(f"Could not parse output: {output}")
        proj_id = match.group(1)
        file = Path(subprocess.check_output(["nb", "ls", "--no-color", "--paths", "--no-id", proj_id]).decode().strip())
        assert file.exists()
        # Sync nb
        subprocess.check_output(["nb", "sync", "--no-color", file])
        print(f"Created project {name} file {file}")
        return file

    def nb_logfile(self) -> Path:
        """Return the path to the project's logfile, creating it if necessary."""
        assert self.file is not None
        logfile = self.file.parent / f"{self.file.stem}.md"
        if not logfile.exists():
            new_logfile = self.nb_add_file(self.name, "project.md", self.data.description or "")
            assert new_logfile == logfile  # Sanity check to prevent infinite logfiles
        assert logfile.exists()
        return logfile


def get_projects() -> dict[str, Project]:
    """Return a mapping of project names to their project by querying nb."""
    # Someday we may want to avoid opening each project file and build lazy loading but for now just grab them all.
    output = subprocess.check_output(["nb", "ls", "--no-color", "--type=project.yaml", "--paths", "--no-id"]).decode()

    if not output:
        # I've seen this happen when the git index is messed up.
        raise RuntimeError("Could not get projects, check `nb status`, there may be a git index issue.")

    # If there are no items, it will print all sorts of nonsense. Scan for "0 project.yaml items".
    if "0 project.yaml items" in output:
        return {}

    paths = [Path(path) for path in output.splitlines()]
    projects = [Project.by_file(path) for path in paths]
    return {project.name: project for project in projects}
