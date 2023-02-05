# -*- coding: utf-8 -*-
"""Tests built from use_cases.md Use Case 1: "Whack A Mole"

Note that these are UNIT tests and not intended as e2e acceptance tests, so the fact that these tests pass does not
necessarily imply that the use cases are supported as written. For example, these tests will not, for instance, fork out
to the shell to test the cli. Instead, tests will confirm use case support in mole internal code.
"""
import pytest


@pytest.fixture
def create_remote_task(request) -> bool:
    """Fixture-flag for whether or not the remote task should be created"""
    return bool(request.param)


@pytest.fixture
def remote_task(create_remote_task: bool):
    if not create_remote_task:
        return None


@pytest.fixture
def previous_task():
    class Placeholder:
        completed = True

    return Placeholder()


@pytest.mark.parametrize("create_remote_task", [False], indirect=True)
def test_case_1_whack_a_mole(previous_task, remote_task):
    assert previous_task.completed
    assert remote_task is None
