# notebook.py - API for nb-cli
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from pendulum import Date, DateTime

from .projects import Project

When = Union[Date, DateTime]


@dataclass
class Logbook:
    project: Optional[Project]

    def edit_log(self, when: Optional[When] = None, preamble: Optional[str] = None):
        """Open the given day's log in $EDITOR.

        In order to avoid locking the notebook, this works 'around' nb by opening the file directly, manually syncing when the editor exits. That means that this call blocks while the editor is still running. Nothing is done to avoid race conditions with other writing or syncing processes.

        If the log for the given date or datetime does not exist, it is created. If no date or datetime is given, the current datetime is used.

        If preamble is anything other than None, a preamble markdown header is appended to the log for the given date or datetime. If the preamble is a non-empty string, it will be appended to the generated header after a colon.
        """
        if when is None:
            when = DateTime.now()
        log_path = self.get_or_create_log(when)
        if preamble is not None:
            header = self.make_header(when, preamble)
            # Technically this could have been done in the same call made by get_or_create_log when it creates the file,
            # but then you need to handle the case where the file already exists, and it's just easier to do it here.
            # Compared to normal file I/O this is extremely expensive, but it's not like we're doing this in a loop.
            subprocess.run(["nb", "edit", log_path, "--content", header], check=True)
        subprocess.run(["nb", "open", log_path], check=True)
        subprocess.run(["nb", "sync"])

    def append_log(self, entry: str, when: Optional[When] = None, preamble: Optional[str] = None):
        """Like edit_log, but instead of opening in $EDITOR, just append a new entry and sync. A header is always printed."""
        if when is None:
            when = DateTime.now()
        log_path = self.get_or_create_log(when)
        header = self.make_header(when, preamble)
        content = f"{header}\n\n{entry}"
        subprocess.run(["nb", "edit", log_path, "--content", content], check=True)
        subprocess.run(["nb", "sync"])

    def append_log_header(self, when: Optional[DateTime] = None, preamble: Optional[str] = None):
        """Like append_log, but just the header, and no sync"""
        if when is None:
            when = DateTime.now()
        log_path = self.get_or_create_log(when)
        header = self.make_header(when, preamble, time_only=True)
        subprocess.run(["nb", "edit", log_path, "--content", header], check=True)

    def append_log_footer(self, when: Optional[DateTime] = None):
        """Print an h3 closing header to the day's log and sync."""
        if when is None:
            when = DateTime.now()
        log_path = self.get_or_create_log(when)
        footer = f"### {when.format('HH:mm')} Session closed"
        subprocess.run(["nb", "edit", log_path, "--content", footer], check=True)
        subprocess.run(["nb", "sync"])

    def make_header(self, when: When, preamble: Optional[str], time_only: bool = False) -> str:
        """Return a markdown header for the given date or datetime."""
        # TODO it looks bad to have the full date on each entry but I can't untangle the datetime mess right now
        if isinstance(when, DateTime):
            if time_only:
                header = f"## {when.format('HH:mm')}"
            else:
                header = f"## {when.format('dddd, MMMM Do, YYYY HH:mm')}"
        elif isinstance(when, Date):
            if time_only:
                raise ValueError("Cannot make time-only header for Date, pass DateTime instead")
            header = f"## {when.format('dddd, MMMM Do, YYYY')}"
        else:
            raise TypeError(f"Unexpected type {type(when)} for when")

        if preamble:
            header += f": {preamble}"

        return header

    def get_or_create_log(self, when: When) -> str:
        day = when.date() if isinstance(when, DateTime) else when
        title = day.strftime("%A, %B %d, %Y")

        # Find the proper log_path
        if self.project is not None:
            in_right_dir = False
            if self.project.data.cwd is not None:
                proj_dir = Path(self.project.data.cwd).expanduser()
                cwd = Path.cwd()
                in_right_dir = proj_dir == cwd or proj_dir in cwd.parents

            has_local_logbook = False
            if in_right_dir:  # Avoid unnecessary subprocess calls with this one weird if
                has_local_logbook = (
                    subprocess.run(["nb", "notebooks", "--local"], capture_output=True).returncode == 0
                    if in_right_dir
                    else False
                )

            if has_local_logbook:
                notebook = "local"
            else:
                notebook = self.get_or_create_global_notebook()

            log_dir = self.project.data.log_dir
            if log_dir is None:
                log_path = f"{notebook}:{title}.log.md"
            else:
                log_path = f"{notebook}:{log_dir}/{title}.log.md"
        else:
            log_path = f"{title}.log.md"

        # If the log doesn't exist, create it
        is_new_entry = subprocess.run(["nb", "list", "--type=log.md", log_path], capture_output=True).returncode == 1
        if is_new_entry:
            # TODO figure out a better way to handle this content 'hack'
            subprocess.run(["nb", "add", log_path, "--title", title, "--type=log.md", "--content", " "], check=True)

        return log_path

    def get_or_create_global_notebook(self) -> str:
        """Return the global notebook for the given project, creating it if necessary.

        Does not check for a local logbook, which may mask the global notebook if it exists and is configured.
        """
        if self.project is None:
            raise ValueError("Cannot get global notebook without a project")
        notebooks = [line.strip() for line in subprocess.check_output(["nb", "notebooks"], text=True).splitlines()]
        if self.project.session_name not in notebooks:
            subprocess.run(["nb", "notebooks", "add", self.project.session_name], check=True)
        return self.project.session_name
