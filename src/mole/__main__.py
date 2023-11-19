# -*- coding: utf-8 -*-
import os
import sys

import typer
from openai import OpenAI
from typerassistant import TyperAssistant

from .cli import app
from .secrets import get_secret


# Default entrypoint for poetry run mole here:  (specified in pyproject.toml)
def main():
    if os.getenv("VIRTUAL_ENV") and sys.argv[0].endswith("mole"):
        typer.echo(
            "🐭 Error: detected poetry environment AND pipx entrypoint, this will surely cause PYTHONPATH conflicts, aborting"
        )
        sys.exit(1)

    client = OpenAI(api_key=get_secret("OpenAI", "credential", vault="blumeops"))

    # Enable automatic OpenAI Assistant integration
    assistant = TyperAssistant(
        app,
        replace=True,  # For now, while I iron out the kinks
        client=client,
        instructions="The user is named Erich Blume. Erich wrote mole to be a personal automation tool using python and the Typer CLI. The assistant has access to the mole CLI via functions. Please help Erich with his query. If no function exists to help Erich's query, consider suggesting a small typer command to supply that function. Be concise. Thanks!",
    )
    app.assistant = assistant

    app()


# Default entrypoint for python -m mole here:
if __name__ == "__main__":
    main()
