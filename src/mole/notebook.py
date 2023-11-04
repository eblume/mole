# notebook.py - API for nb-cli
import subprocess
from typing import Optional

from pendulum import DateTime


def add_log(entry: Optional[str], subtitle: Optional[str] = None, when: Optional[DateTime] = None) -> None:
    """Add an entry to the day's log."""

    if when is None:
        when = DateTime.now()
    title = when.strftime("%A, %B %d, %Y")
    filename = f"{when.format('YYYY-MM-DD')}.log.md"
    is_new_entry = subprocess.run(["nb", "list", "--type=log.md", filename], capture_output=True).returncode == 1
    content = f"## {when.format('HH:mm')} {subtitle or ''}\n\n{entry or ''}"

    if is_new_entry:
        subprocess.check_output(["nb", "add", filename, "--title", title, "--content", content, "--type=log.md"])
    else:
        subprocess.check_output(["nb", "edit", filename, "--content", content])

    if not entry:
        # Because no entry was given, we need to finish in $EDITOR. We would normally use --edit which is exactly what
        # this is for (note that this is SEPERATE from nb add vs nb edit), but --edit mode takes out a global lock on nb
        # while the buffer is open, and I like to keep my log open all day sometimes. So instead we use nb open.
        # (I filed a bug on this, no link handy)
        subprocess.run(["nb", "open", filename])

    subprocess.check_output(["nb", "sync"])
