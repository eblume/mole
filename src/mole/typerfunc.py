import sys
from dataclasses import dataclass
from typing import Optional

from typer import Typer
from typer.main import get_command_from_info


# The best usage guide seems to be:
#   https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models


@dataclass
class ParameterSpec:
    name: str
    description: str
    required: bool
    default: Optional[str] = None
    enum: Optional[list[str]] = None


@dataclass
class FunctionSpec:
    name: str
    description: str
    parameters: list[ParameterSpec]

    def dict(self) -> dict:
        struct = {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {  # This is now technically a JSONSchema object
                    "type": "object",
                    "properties": {
                        param.name: {
                            "type": "string",  # TODO other types?
                            "description": param.description,
                            "default": param.default or "None",
                        }
                        for param in self.parameters
                    },
                    "required": [param.name for param in self.parameters if param.required],
                },
            },
        }

        # enum processing - do this in a second pass to avoid empty enums
        for param in self.parameters:
            if param.enum:
                struct["function"]["parameters"]["properties"][param.name]["enum"] = list(param.enum)
        return struct


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
        breakpoint()

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
        )
        functions.append(spec)

    return functions
