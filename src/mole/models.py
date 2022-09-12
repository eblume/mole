# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class Task:
    """A basic model representing a Task in some state.

    The actual concrete meaning of what a Task object represents is dependent on context, which may in some cases
    be provided by the subtype of the Task object (if subclassing is used). For instance, in a configuration script, a Task
    object is likely to represent the intentional (partial) state of a Task that the user would like to create or modify. In
    contrast, a Task object created by a StoreUpdater from an API update from a remote is instead likely to represent the
    present state of that Task object as understood by the remote API.

    It is up to the caller to understand the correct context of a Task.

    NB: Avoid adding functional logic to this class unless it is absolutely certain that it applies in ALL potential contexts.
    """

    name: str
