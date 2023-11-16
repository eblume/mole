import sys
from dataclasses import dataclass, field, KW_ONLY
from typing import Iterable, Optional

from typer import Typer
from typer.main import get_command_from_info

from .assistant import Assistant, FunctionSpec, ParameterSpec


def typerfunc(app: Typer, command_prefix: str = None) -> list[FunctionSpec]:
    """Returns a list of FunctionSpecs describing the CLI of app.

    This function recurses on command groups, with a command_prefix appended to the beginning of each command name in
    that group.
    """
    if command_prefix is None:
        command_prefix = app.info.name or sys.argv[0]

    functions: list[FunctionSpec] = []

    for command_info in app.registered_commands:
        command = get_command_from_info(
            command_info=command_info,
            pretty_exceptions_short=app.pretty_exceptions_short,
            rich_markup_mode=app.rich_markup_mode,
        )
        fullname = f"{command_prefix}.{command.name}"
        if isinstance(command, Typer):
            # Recurse on command groups
            functions.extend(typerfunc(command, command_prefix=fullname))
            continue

        # Extract callback signature for parameters.
        params = []
        for param in command.params:
            descr = param.help or command_info.callback.__doc__ or "No description available"

            param_spec = ParameterSpec(
                name=param.name,
                description=descr,
                default=param.default,
                required=param.required,
            )

            params.append(param_spec)

        spec = FunctionSpec(
            name=fullname,
            description=command.help,
            parameters=params,
            action=command_info.callback,  # command_info.callback is the user function, command.callback is the internal click wrapper.
        )
        functions.append(spec)

    return functions


@dataclass
class AppAssistant(Assistant):
    """An Assistant generated from a Typer app."""

    app: Typer
    _: KW_ONLY
    instructions: str = "The agent is an interface to a python Typer CLI. The tools available correspond to typer commands. Please help the user with their queries, executing CLI functions as needed. Be concise."
    name: Optional[str] = field(init=False, default=None)

    def __post_init__(self):
        self.name = self.app.info.name or sys.argv[0]
        super().__post_init__()

    def functions(self) -> Iterable[FunctionSpec]:
        """Generate FunctionSpecs from the Typer app."""
        yield from super().functions()  # currently a non-op but may be useful to others
        yield from typerfunc(self.app)
