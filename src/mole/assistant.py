import json
import time
from dataclasses import dataclass, field
from typing import Protocol, Optional, Any, Callable
from collections.abc import Iterable

import typer
from openai import OpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.thread import Thread

from .todoist import create_task
from .secrets import get_secret


CLIENT = OpenAI(api_key=get_secret("OpenAI", "credential", vault="blumeops"))
THREAD = None


class FileWithID(Protocol):
    @property
    def id(self):
        ...


@dataclass
class Tool:
    type: str

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type}


@dataclass
class Function(Tool):
    @dataclass
    class PropertySpec:
        description: str
        type: str = "string"
        enum: Optional[list[str]] = None
        required: bool = False
        # There could be other respected fields, OpenAI doesn't publish this schema. See:
        # https://github.com/openai/openai-python/blob/main/src/openai/types/shared/function_parameters.py

    name: str
    description: str
    parameters: dict[str, PropertySpec]
    action: Callable[..., Any]  # TODO type this better
    type: str = field(init=False, default="function")

    def __post_init__(self):
        self.type = "function"

    def to_dict(self) -> dict[str, Any]:
        # TODO either find a way to use openai.types better for this, OR open source this as a library
        spec = super().to_dict()
        funcspec = {"name": self.name, "description": self.description}
        parameters = {
            "type": "object",
            "properties": {},
        }

        required = []
        for name, param in self.parameters.items():
            vals = {
                "description": param.description,
                "type": param.type,
            }
            if param.enum is not None:
                vals["enum"] = param.enum
            parameters["properties"][name] = vals
            if param.required:
                required.append(name)

        if required:
            parameters["required"] = required

        funcspec["parameters"] = parameters
        spec["function"] = funcspec
        return spec


def compile_tools() -> Iterable[Tool]:
    # TODO modularize

    # create task
    def _call_todoist(id: str, **kwargs):
        if "name" not in kwargs:
            # TODO smarter validation with error handling using id
            raise ValueError("Missing required parameter 'name'")
        return create_task(kwargs["name"])

    yield Function(
        name="create-task",
        description="Create a task, returning a todoist:// url",
        parameters={
            "name": Function.PropertySpec(
                description="The name of the task",
                type="string",
                required=True,
            ),
        },
        action=_call_todoist,
    )


def make_assistant() -> Assistant:
    # TODO migrations? versioning?

    for assistant in CLIENT.beta.assistants.list():
        if assistant.name == "Hermes":
            typer.echo("Found existing assistant")
            return assistant

    typer.echo("Creating new assistant")
    return CLIENT.beta.assistants.create(
        name="Hermes",
        instructions="Assist Erich Blume by parsing the output of his voice memos. Take actions as needed using tools, or if none are applicable, do nothing.",
        tools=[tool.to_dict() for tool in compile_tools()],
        model="gpt-4-1106-preview",
    )


def make_thread() -> Thread:
    # The threads API doesn't make it easy to retrieve existing threads, you have to know the specific thread's ID ahead
    # of time. Eventually we can try and store that in the day's log or in some other context store, but for now we'll
    # just start a new thread once per python process. Note that pricing is typically per-thread (or per-session which
    # is per-thread? confusing. Details: https://help.openai.com/en/articles/8550641-assistants-api)
    #
    # API docs: https://platform.openai.com/docs/api-reference/threads/getThread
    #
    # TODO: Restore thread context (see above note)
    global THREAD
    if THREAD is None:
        THREAD = CLIENT.beta.threads.create()
    return THREAD


def add_message(thread: Thread, content: str, role: str = "user"):
    # TODO return type?
    # TODO support full API https://platform.openai.com/docs/api-reference/messages
    return CLIENT.beta.threads.messages.create(
        thread_id=thread.id,
        role=role,
        content=content,
    )


def run_thread(thread: Thread, assistant: Assistant):
    # TODO support re-running, retrieving runs, etc. For now, we will pretend like every assistant+thread has one run,
    # which this function will block on until that run reaches a stopping point. If the current run is 'cancelled',
    # 'failed', 'completed', or 'expired' then this function will simply create a new run.
    TERMINAL_STATES = {"cancelled", "failed", "completed", "expired"}
    BLOCKED_STATES = TERMINAL_STATES | {"requires_action"}

    thread_runs = CLIENT.beta.threads.runs.list(thread.id)  # Defaults to most recent first
    current_run = None
    for run in thread_runs:
        if run.status not in BLOCKED_STATES:
            current_run = run
            break
    if current_run is None:
        # Note that we could specify new model, instruction, tools, or metadata here
        current_run = CLIENT.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)

    # Rebuild the func list so we can call them
    funcs = {}
    for tool in compile_tools():
        if tool.type == "function":
            funcs[tool.name] = tool

    for iterations in range(10):
        # Update the status
        current_run = CLIENT.beta.threads.runs.retrieve(thread_id=thread.id, run_id=current_run.id)

        match current_run.status:
            case "queued" | "in_progress":
                typer.echo(f"Run is '{current_run.status}', waiting 10s...")
                time.sleep(10)
                iterations -= 1  # We won't count a queued iteration

            case "requires_action":
                calls = current_run.required_action.submit_tool_outputs.tool_calls
                results = []
                for call in calls:
                    if call.type == "function":  # for now always true
                        name = call.function.name
                        if name not in funcs:
                            raise ValueError(f"Unknown function {name}")

                        args = json.loads(call.function.arguments)
                        typer.echo(f"Calling {name} with args {args}")
                        result = funcs[name].action(call.id, **args)
                        typer.echo(f"Result: {result}")
                        results.append({"tool_call_id": call.id, "output": result})
                if results:
                    current_run = CLIENT.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id, run_id=current_run.id, tool_outputs=results
                    )

            case "completed":
                messages = list(CLIENT.beta.threads.messages.list(thread_id=thread.id))
                # messages[0] is (always?) the assistant response. We may need to be smarter or even use Run Steps API.
                #
                # Also there's all this stuff with message contexts, but that will come later.
                content = messages[0].content
                assert len(content) == 1
                assert content[0].type == "text"
                assert len(content[0].text.annotations) == 0
                typer.echo(f"Assistant says: {content[0].text.value}")
                return

            case "cancelling" | "cancelled" | "failed" | "expired":
                typer.echo(f"Run completed with status {current_run.status}")
                return

            case _:
                typer.echo(f"Unhandled run status {current_run.status}")
                return
    typer.echo(f"Run timed out after {iterations} iterations")
