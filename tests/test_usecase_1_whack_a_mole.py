# -*- coding: utf-8 -*-
"""Tests built from use_cases.md Use Case 1: "Whack A Mole"

Note that these are UNIT tests and not intended as e2e acceptance tests, so the fact that these tests pass does not
necessarily imply that the use cases are supported as written. For example, these tests will not, for instance, fork out
to the shell to test the cli. Instead, tests will confirm use case support in mole internal code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Type

from _pytest.fixtures import SubRequest
import pytest

from mole.actions import Actions
from mole.remote import Remote, RemoteConfig
from mole.session import Session
from mole.task import Task


@dataclass
class DummyRemoteConfig(RemoteConfig):
    pass


class DummyRemote(Remote[DummyRemoteConfig]):
    def __init__(self, tasks: list[Task], config: DummyRemoteConfig):
        self._tasks = tasks
        self._config = config

    @classmethod
    def from_config(cls: Type[DummyRemote], config: DummyRemoteConfig) -> DummyRemote:
        return cls([], config)

    def get_tasks(self) -> list[Task]:
        return self._tasks

    def create_task(self, task: Task):
        self._tasks.append(task)


@pytest.fixture(params=[True, False])
def create_previous_task(request: SubRequest) -> bool:
    """Fixture-flag for whether or not the already-completed task should be created"""
    return bool(request.param)


@pytest.fixture(params=[True, False])
def create_next_task(request: SubRequest) -> bool:
    """Fixture-flag for whether or not the not-yet-completed task should be created"""
    return bool(request.param)


@pytest.fixture
def next_task(remote: Remote):
    """The 'next' task represents a potentially existing already (or not!) task.

    If it exists, it represents a task created just prior to the test running.

    If it does not exist, then it represents a contract that no such task exists, ie the test should make it now.
    """
    tasks = remote.get_tasks()
    for task in tasks:
        if task.name == "Whack-a-Mole" and task.completed == False:
            return task
    return None


@pytest.fixture
def remote(remote_config: DummyRemoteConfig, create_previous_task: bool, create_next_task: bool):
    new_remote = DummyRemote.from_config(remote_config)
    if create_previous_task:
        new_remote.create_task(Task("Whack-a-Mole", completed=True))
    if create_next_task:
        new_remote.create_task(Task("Whack-a-Mole", completed=False))
    return new_remote


@pytest.fixture
def remote_config():
    return DummyRemoteConfig()


@pytest.fixture
def previous_task(remote: Remote):
    """The 'previous' task represents some task "in the past", prior to the 'next' task."""
    tasks = remote.get_tasks()
    for task in tasks:
        if task.name == "Whack-a-Mole" and task.completed == True:
            return task
    return None


@pytest.fixture
def session(remote: Remote):
    return Session(remote=remote)


@pytest.mark.parametrize(
    "create_next_task,should_create_task",
    [(True, False), (False, True)],
    indirect=["create_next_task"],
)
def test_case_1_should_create_whack_task(
    create_next_task, should_create_task, previous_task, next_task, session
):
    """Given a variety of setup conditions, determine whether or not a mole whacking task should be created."""
    # Precondition: if there's a previously defined task, it's completed
    if previous_task is not None:
        assert previous_task.completed

    # Precondition: if we should have made a task "now", it exists.
    if create_next_task:
        assert next_task is not None
    else:
        assert next_task is None

    # Create the expectation - an empty action set, or a single create action
    expected_actions = Actions()
    if should_create_task:
        expected_actions.create_task.append(Task(name="Whack-a-Mole", completed=False))

    actions = session.determine_actions()
    assert actions == expected_actions


@pytest.mark.parametrize("create_next_task", [False], indirect=True)
def test_case_1_would_remotely_crate_whack_ask(create_next_task, session, mocker):
    mocker.patch.object(session.remote, "create_task")

    actions = session.determine_actions()
    session.resolve_actions(actions)

    assert session.remote.create_task.called_once_with(Task(name="Whack-a-Mole", completed=False))
