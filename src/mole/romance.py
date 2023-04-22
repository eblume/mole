"""Rules and actions for romance'n my wife."""
import typer

from .todoist import TodoistRemote
from .models import Task

def check_special_plan(remote: TodoistRemote) -> None:
    """Check for special plans and add them to the todoist inbox."""
    label = "special_plan"
    special_plan_tickets = remote.get_tasks(label=label)
    if not special_plan_tickets:
        remote.create_task(Task("Make a special plan", labels=[label]), project_name="Allison")
        typer.secho("❤️ Added a special plan", fg=typer.colors.BLUE)
    else:
        typer.secho("❤️ Special plan already exists", fg=typer.colors.GREEN)
