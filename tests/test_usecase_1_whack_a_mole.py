# -*- coding: utf-8 -*-
"""Tests built from use_cases.md Use Case 1: "Whack A Mole"

Note that these are UNIT tests and not intended as e2e acceptance tests, so the fact that these tests pass does not
necessarily imply that the use cases are supported as written. For example, these tests will not, for instance, fork out
to the shell to test the cli. Instead, tests will confirm use case support in mole internal code.
"""
from __future__ import annotations

from dataclasses import dataclass
import datetime as dt
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

    def get_tasks(
        self, date: Optional[dt.date] = None, name: str = "", completed: bool = False
    ) -> list[Task]:
        if date is None:
            date = dt.date.today()
        return [
            task
            for task in self._tasks
            if task.date == date and task.name == name and task.completed == completed
        ]

    def create_task(self, name: str, date: Optional[dt.date] = None, completed: bool = False):
        if date is None:
            date = dt.date.today()
        self._tasks.append(Task(name=name, completed=completed, date=date))


@pytest.fixture(params=[True, False])
def create_previous_task(request: SubRequest) -> bool:
    """Fixture-flag for whether or not the already-completed task should be created"""
    return bool(request.param)


@pytest.fixture(params=[True, False])
def create_next_task(request: SubRequest) -> bool:
    """Fixture-flag for whether or not the not-yet-completed task should be created"""
    return bool(request.param)


@pytest.fixture
def next_task(remote: Remote, today: dt.date):
    """The 'next' task represents a potentially existing already (or not!) task.

    If it exists, it represents a task created just prior to the test running.

    If it does not exist, then it represents a contract that no such task exists, ie the test should make it now.
    """
    tasks = remote.get_tasks(date=today, name="Whack-a-Mole", completed=False)
    if len(tasks) > 0:
        return tasks[0]
    return None


@pytest.fixture
def today():
    # Fixture used so we can eventually test with assumptions about the date
    return dt.date.today()


@pytest.fixture
def remote(
    remote_config: DummyRemoteConfig,
    create_previous_task: bool,
    create_next_task: bool,
    today: dt.date,
):
    new_remote = DummyRemote.from_config(remote_config)
    if create_previous_task:
        new_remote.create_task("Whack-a-Mole", completed=True, date=today)
    if create_next_task:
        new_remote.create_task("Whack-a-Mole", completed=False, date=today)
    return new_remote


@pytest.fixture
def remote_config():
    return DummyRemoteConfig()


@pytest.fixture
def previous_task(remote: Remote, today: dt.date):
    """The 'previous' task represents some task "in the past", prior to the 'next' task."""
    tasks = remote.get_tasks(date=today, name="Whack-a-Mole", completed=True)
    if len(tasks) > 0:
        return tasks[0]
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
    create_next_task, should_create_task, previous_task, next_task, session, today
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
        expected_actions.create_task.append(Task(name="Whack-a-Mole", date=today, completed=False))

    actions = session.determine_actions()
    assert actions == expected_actions
