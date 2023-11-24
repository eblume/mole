from __future__ import annotations

import re
import subprocess
from dataclasses import InitVar, asdict, dataclass, field
from pathlib import Path

import typer
from yaml import dump, load

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper, Loader


app = typer.Typer(help="Manage projects", no_args_is_help=True)


@app.command()
def list():
    """List all projects"""
    for project in get_projects().values():
        typer.echo(project.name)


@app.command()
def create(name: str):
    """Create a new project"""
    Project.create(name)


@dataclass
class Project:
    name: str
    file: InitVar[Path] = field(init=False)

    @classmethod
    def load(cls, file: Path) -> Project:
        """Load a project from a file"""
        attrs = load(file.read_text(), Loader=Loader)
        # TODO handle migrations, etc.
        proj = cls(**attrs)
        proj.file = file
        return proj

    @classmethod
    def create(cls, name: str) -> Project:
        """Create a new project"""
        if not re.match(r"^[a-zA-Z0-9_\- ]+$", name):
            raise ValueError(f"Project name {name} is invalid")

        if name in get_projects():
            raise ValueError(f"Project {name} already exists")

        # First we create a 'dummy' project to get the YAML representation
        dummy = cls(name=name)
        data = dump(asdict(dummy), Dumper=Dumper)

        output = subprocess.check_output(
            ["nb", "add", "--no-color", "--type=project.yaml", "--title", name], input=data.encode()
        ).decode()
        # Example:
        # Added: [123] foo.project.yaml "foo"
        # We want the 123
        match = re.match(r"Added: \[(\d+)\]", output)
        proj_id = match.group(1)

        # Create the project metadata file
        file = Path(
            subprocess.check_output(["nb", "ls", "--no-color", "--type=project.yaml", "--paths", "--no-id", proj_id])
            .decode()
            .strip()
        )
        assert file.exists()
        # Sync nb
        subprocess.run(["nb", "sync", "--no-color", file], check=True)

        # Finally, load the created file and return that.
        return Project.load(file)

    def write(self):
        """Write the project to disk. This is not thread-safe."""
        # Race condition: if the file is modified between the read and the write, the changes will be lost, etc.
        self.file.write_text(dump(asdict(self), Dumper=Dumper))
        subprocess.run(["nb", "sync", "--no-color", self.file], check=True)


def get_projects() -> dict[str, Project]:
    """Return a mapping of project names to their project by querying nb."""
    # Someday we may want to avoid opening each project file and build lazy loading but for now just grab them all.
    output = subprocess.check_output(["nb", "ls", "--no-color", "--type=project.yaml", "--paths", "--no-id"]).decode()

    # If there are no items, it will print all sorts of nonsense. Scan for "0 project.yaml items".
    if "0 project.yaml items" in output:
        return {}

    paths = [Path(path) for path in output.splitlines()]
    projects = [Project.load(path) for path in paths]
    return {project.name: project for project in projects}
