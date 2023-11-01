# -*- coding: utf-8 -*-
import logging
import os
import sys

import typer
from rich.console import Console
from rich.table import Table


app = typer.Typer(
    help="Mole is a tool for automating my life.",
    no_args_is_help=True,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


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
def airflow(port: int = 8081):
    """Run apache airflow locally on the specified port"""
    from .airflow import run_airflow

    run_airflow(port)


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    if os.getenv("VIRTUAL_ENV") and sys.argv[0].endswith("mole"):
        typer.echo(
            "🐭 Error: detected poetry environment AND pipx entrypoint, this will surely cause PYTHONPATH conflicts, aborting"
        )
        sys.exit(1)
    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
