import pytest
from _pytest.capture import CaptureResult


from mole.work import work
from mole.chores import ChoreDefinition


@pytest.fixture
def chore_definitions() -> list[ChoreDefinition]:
    return [
        ChoreDefinition(name="Fizz", interval_days=3),
        ChoreDefinition(name="Buzz", interval_days=5),
    ]


@pytest.fixture
def work_capsys(
    capsys: pytest.CaptureFixture[str], chore_definitions: list[ChoreDefinition]
) -> CaptureResult[str]:
    """This fixture actually runs the proposed work"""
    # It is intended that this fixture will be highly parameterized for these tests.
    work(chores=chore_definitions)
    return capsys.readouterr()


@pytest.fixture
def captured_output(work_capsys: CaptureResult[str]) -> str:
    return work_capsys.out


def test_all_done(captured_output: str):
    assert captured_output.endswith("All Done!\n")


def test_some_chores(captured_output: str, chore_definitions: list[ChoreDefinition]):
    for chore in chore_definitions:
        assert chore.name in captured_output
