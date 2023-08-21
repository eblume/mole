import tempfile
import datetime as dt

import typer


app = typer.Typer(help="YNAB-related commands", no_args_is_help=True)


@app.command()
def backup():
    """Back up YNAB data to the local filesystem"""
    last_year = dt.date.today() - dt.timedelta(days=365)
    raise NotImplemented("not done yet")
