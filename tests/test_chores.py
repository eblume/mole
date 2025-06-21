"""Tests for Chores, and for the ChoreState system."""

import pendulum
import pytest

from mole.chores import ChoreDefinition, ChoreState


@pytest.fixture
def chore_definitions() -> list[ChoreDefinition]:
    return [
        ChoreDefinition(name="Fizz", interval_days=3),
        ChoreDefinition(name="Buzz", interval_days=5),
    ]


@pytest.fixture
def chore_state(chore_definitions: list[ChoreDefinition]) -> ChoreState:
    state = ChoreState.from_volatile_memory()
    state.chore_definitions = chore_definitions
    return state


def test_day_zero_all_chores_due(
    chore_definitions: list[ChoreDefinition], chore_state: ChoreState
):
    # Assuming that all chores do not have any starting-date constraints (not tested)
    assert len(chore_definitions) == len(chore_state.due_chores)


def test_no_chores_due_after_all_marked_done(
    chore_definitions: list[ChoreDefinition], chore_state: ChoreState
):
    for chore in chore_definitions:
        chore_state.mark_complete(chore.name)


def test_skip_day_still_due(
    chore_state: ChoreState, chore_definitions: list[ChoreDefinition], freezer
):
    # precondition check
    assert len(chore_definitions) == len(chore_state.due_chores)
    # next day
    when = pendulum.now()
    freezer.move_to(when.add(days=1).strftime("%Y-%m-%d"))
    # test
    assert len(chore_definitions) == len(chore_state.due_chores)


@pytest.fixture(params=list(range(16)))
def fizzbuzz_day(chore_state: ChoreState, freezer, request) -> int:
    """Time-travelling fizzbuzz for chores"""
    when = pendulum.now()
    days = 0
    freezer.move_to(when.strftime("%Y-%m-%d"))
    for _ in range(request.param):
        for chore in chore_state.due_chores:
            chore_state.mark_complete(chore.name)
        when = when.add(days=1)
        days += 1
        freezer.move_to(when.strftime("%Y-%m-%d"))
    return days


def test_fizzbuzz_when_completing_chores(
    fizzbuzz_day: int, chore_definitions: list[ChoreDefinition], chore_state: ChoreState
):
    # This test is predicated on chores being completed on the day that
    # they were due. A better test might also model skipping days, etc.
    chores_due = {c.name for c in chore_state.due_chores}
    for chore in chore_definitions:
        if fizzbuzz_day % chore.interval_days == 0:
            assert chore.name in chores_due
            # Just for fun:
            print(chore.name)


@pytest.mark.parametrize("interval_days", [1, 2, 3, 7, 14])
def test_chore_reoccurs_exactly_after_interval(
    chore_state: ChoreState, freezer, interval_days
):
    # define a single chore with the given interval
    chore = ChoreDefinition(name="TestChore", interval_days=interval_days)
    chore_state.chore_definitions.append(chore)

    # set “today” to a fixed date
    today = pendulum.now().date()
    freezer.move_to(today.strftime("%Y-%m-%d"))

    # on day 0 it must be due
    due_names = [c.name for c in chore_state.due_chores]
    assert chore.name in due_names

    # mark it complete on day 0
    chore_state.mark_complete("TestChore")

    # on each day before interval_days, it must NOT be due
    for offset in range(1, interval_days):
        freezer.move_to(today.add(days=offset).strftime("%Y-%m-%d"))
        assert chore.name not in chore_state.due_chores, (
            f"Chore became due too early on day {offset} for interval={interval_days}"
        )

    # on exactly interval_days later, it must be due again
    freezer.move_to(today.add(days=interval_days).strftime("%Y-%m-%d"))
    due_names = [c.name for c in chore_state.due_chores]
    assert chore.name in due_names, (
        f"Chore did not reappear on day {interval_days} for interval={interval_days}"
    )
