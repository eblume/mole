"""Utilities for interacting with Zellij, a rust-based terminal multiplexer."""
from __future__ import annotations

from dataclasses import KW_ONLY, dataclass, field
from typing import Optional, Union

from kdl.types import Document, Node
from typing_extensions import TypedDict

## Zellij KDL types for Python via dataclasses
#
# A short incomplete list of remaining work:
# - Split up Pane and ContainerPane (and maybe TabPane) into separate classes, Pane should have no children maybe?
# - Make sure all documented properties and arguments are supported
# - Full config support (currently only session_serialization is supported)
# - Load from KDL - currently only dumping to KDL is supported, but this should be "easy"
# - Layout directories
# - pane and tab templates
# - keybinds
# - plugin API (would be cool to have a python plugin API for Zellij that auto-injects itself)
# - rethink how to express the sometimes-allowed alternate syntaxes for child node 'arguments' vs prop 'arguments'


@dataclass
class Pane:
    """A Zellij pane."""

    class Props(TypedDict, total=False):
        """`props` for a Zellij pane/KDL node.

        This is defined as a TypedDict interior to the Pane class so that:

        1. It can be statically typed.
        2. Subclasses can extend their own properties without rewriting parent property handling.
        3. Dataclass 'fields' (ie python "properties") can be used for arguments and sub-nodes.

        If you don't care about these things, you can simply use a dict.
        """

        # (Quick note: zellij docs mix up 'props' and 'args' and sub-nodes. I am mostly sticking with KDL.)
        size: Optional[Union[int, str]]  # Percentages eg. "50%", or fixed values eg. "1"
        stacked: Optional[bool]
        borderless: Optional[bool]
        focus: Optional[bool]
        name: Optional[str]
        split_direction: Optional[str]

    _: KW_ONLY
    panes: list[Pane] = field(default_factory=list)
    props: Props = field(default_factory=Props)

    def node(self) -> Node:
        child_nodes = [pane.node() for pane in self.panes]

        return Node("pane", props=dict(self.props), nodes=child_nodes)


@dataclass
class Layout:
    """A Zellij layout."""

    class Config(TypedDict, total=False):
        session_serialization: Optional[bool]

    _: KW_ONLY
    config: Config = field(default_factory=Config)
    panes: list[Pane] = field(default_factory=list)

    def dump(self) -> str:
        """Dump the layout to a string."""
        layout = Node("layout", nodes=[pane.node() for pane in self.panes])
        document = Document(nodes=[layout])
        for key, value in self.config.items():
            if value is not None:
                if not isinstance(value, list):
                    value = [value]
                document.nodes.append(Node(key, args=value))
        return str(document)


@dataclass
class PluginPane(Pane):
    """A Zellij plugin pane."""

    location: str

    def node(self) -> Node:
        node = super().node()
        # Note: not location is not a property, but rather a plugin node with a location property
        plugin = Node("plugin", props={"location": self.location})
        node.nodes.append(plugin)
        return node


@dataclass
class CommandPane(Pane):
    """A Zellij command pane.

    The command is specified as a list of strings, where the first string is the command. The remainder will be passed to the pane's 'args' child node.
    """

    command: list[str]

    def node(self) -> Node:
        node = super().node()

        command_node = Node("command", args=[self.command[0]])
        node.nodes.append(command_node)

        args = self.command[1:]
        if args:
            arg_node = Node("args", args=args)  # What a silly line of code
            node.nodes.append(arg_node)

        return node


@dataclass
class TabPane(Pane):
    """A Zellij tab pane."""

    def node(self) -> Node:
        node = super().node()
        node.name = "tab"
        return node
