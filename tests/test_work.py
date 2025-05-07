import pytest
from _pytest.capture import CaptureResult


from mole.work import work


@pytest.fixture
def work_capsys(capsys: pytest.CaptureFixture[str]) -> CaptureResult[str]:
    """This fixture actually runs the proposed work"""
    # It is intended that this fixture will be highly parameterized for these tests.
    work()
    return capsys.readouterr()


@pytest.fixture
def captured_output(work_capsys: CaptureResult[str]) -> str:
    return work_capsys.out


def test_all_done(captured_output: str):
    assert captured_output.endswith("All Done!\n")
