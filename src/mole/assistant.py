import json
from io import StringIO
from contextlib import redirect_stdout
import time
from dataclasses import dataclass, KW_ONLY, field
from typing import Optional, Any, Callable
from collections.abc import Iterable

from openai import OpenAI
from openai.types.beta.assistant import Assistant as RemoteAssistant
from openai.types.beta.thread import Thread
from openai.types.beta.threads.thread_message import ThreadMessage


# The number of times to poll for a run to complete before giving up
MAX_RUN_ITERATIONS = 20


# The number of seconds to sleep between run iterations
RUN_ITERATION_SLEEP = 3


# The best usage guide for function calling seems to be:
#   https://cookbook.openai.com/examples/how_to_call_functions_with_chat_models


@dataclass
class ParameterSpec:
    name: str
    description: str
    required: bool
    default: Optional[str] = None
    enum: Optional[list[str]] = None


# Why not use openai.types.beta.threads.run_create_params.ToolAssistantToolsFunction?
# For one, it's not documented and it's really hard to use programmatically. For another, I want to use this to bind
# functionspec definitions to callable actions, for reversable function<->functionspec lookups.
# TODO find a better way to document this decision and explain it.
@dataclass
class FunctionSpec:
    name: str
    description: str
    parameters: list[ParameterSpec]
    action: Callable[..., Any]

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


@dataclass
class Assistant:
    """An assistant managed remotely via OpenAI's assistant API.

    This class implements the basic lifecycle of an assistant, from CRUD to running a thread. It is intended to be
    subclassed to extend functionality.
    """

    _: KW_ONLY
    client: OpenAI = field(default_factory=OpenAI)
    name: Optional[str] = None
    instructions: str = "Assist the user with their query. Be concise."
    replace: bool = False
    thread_id: Optional[str] = None
    assistant_id: Optional[str] = None

    def __post_init__(self):
        if self.name is None:
            self.name = self.__class__.__name__

        if self.replace or self.assistant_id is None:
            # TODO rethink this, delay making the assistant until we need it.
            self.assistant_id = self.make_assistant().id

    def ask(self, query: str) -> str:
        """Ask the assistant a question, returning the response.

        This may block for the lifecycle of several API requests as well as waiting on remotely managed threads, in fact blocking for several minutes and then succeeding is not uncommon. The caller should make arrangements for multithreading, etc. should it be needed.
        """
        thread = self.thread()
        self.add_message(thread, query)
        self.run_thread(thread)
        messages = list(self.messages(thread))
        # TODO figure out proper context processing with citations, etc.
        content = messages[0].content
        assert len(content) == 1
        assert content[0].type == "text"
        assert len(content[0].text.annotations) == 0
        return content[0].text.value

    def functions(self) -> Iterable[FunctionSpec]:
        """Returns an iterable of FunctionSpecs describing the function calling tools of this assistant."""
        # The base assistant just returns an empty list but almost any real use case will extend this.
        yield from []

    def do_function(self, name: str, **kwargs) -> Any:
        """Execute the given function with the given arguments."""
        for command in self.functions():
            if command.name == name:
                # Capture stdout, print it, and add it to the result
                with redirect_stdout(StringIO()) as buf:
                    result = command.action(**kwargs)
                output = buf.getvalue()
                if output:
                    print(output)
                    result = f"{output}\n{result}"
                return result
                result = command.action(**kwargs)
        raise ValueError(f"Command {name} not found")

    def thread(self) -> Thread:
        """Retrieves the thread this assistant is using, or creates one if none exists."""
        # TODO proper support for multiple threads and resuming threads, etc.
        if self.thread_id is None:
            self.thread_id = self.client.beta.threads.create().id
        return self.client.beta.threads.retrieve(self.thread_id)

    def add_message(self, thread: Thread, content: str, role: str = "user") -> ThreadMessage:
        """Adds a message to the given thread, returning the message."""
        return self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role=role,
            content=content,
        )

    def messages(self, thread: Thread) -> list[ThreadMessage]:
        # TODO it's not clear if this function is actually useful, and it could be setting us up for a problem if we
        # want to rely on the underlying library's pagination support to e.g. NOT retrieve all messages.
        # OTOH it encapsulates concerns well for subclassers.
        return list(self.client.beta.threads.messages.list(thread_id=thread.id))

    def run_thread(self, thread: Thread):
        """Runs the given thread, blocking until it completes.

        See ask() for more details.
        """
        # TODO better docs
        # TODO handle multiple runs, run resuming, etc.? For now we just create a new run every time.
        run = self.client.beta.threads.runs.create(thread_id=thread.id, assistant_id=self.assistant_id)
        iterations = 0
        while iterations < MAX_RUN_ITERATIONS:
            iterations += 1
            time.sleep(RUN_ITERATION_SLEEP)  # Sleep right away, openai is never done immediately

            # TODO figure out logging, this blocks for so long it will probably require some UI feedback
            match run.status:
                case "queued" | "in_progress":
                    run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                    continue
                case "completed":
                    return
                case "requires_action":
                    iterations = 0  # Ball is in our court
                    calls = run.required_action.submit_tool_outputs.tool_calls
                    results = []
                    for call in calls:
                        if call.type == "function":  # for now always true
                            name = call.function.name
                            args = json.loads(call.function.arguments)
                            result = (
                                self.do_function(name, **args) or "Success"
                            )  # TODO better result handling... catch exceptions?
                            results.append({"tool_call_id": call.id, "output": result})
                    if results:
                        run = self.client.beta.threads.runs.submit_tool_outputs(
                            thread_id=thread.id, run_id=run.id, tool_outputs=results
                        )
                case "cancelling" | "cancelled" | "failed" | "expired":
                    raise RuntimeError(f"Run failed with status {run.status}")
                case _:
                    raise RuntimeError(f"Unexpected status {run.status}")

    def make_assistant(self) -> RemoteAssistant:
        # We would prefer to query for assistants of the given name, but the API doesn't support that.
        assistants = list(self.client.beta.assistants.list())
        for assistant in assistants:
            if assistant.name == self.name:
                if self.replace:
                    self.client.beta.assistants.delete(assistant.id)
                else:
                    return assistant
        return self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructions,
            tools=[tool.dict() for tool in self.functions()],
            model="gpt-4-1106-preview",
        )

    def delete_assistant(self):
        """Delete the assistant from OpenAI."""
        self.client.beta.assistants.delete(self.assistant_id)
