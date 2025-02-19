import pytest
import os
from mole.todoist import create_task, delete_task, task_exists, get_task

pytestmark = pytest.mark.skipif(
    os.getenv("INTEGRATION_MODE") != "true", reason="Integration mode not enabled"
)


@pytest.fixture
def labels(request: pytest.FixtureRequest) -> list[str]:
    param: str = request.param or ""
    return param.split(",") + ["test"]


@pytest.fixture
def task(labels):
    task_id = create_task("Test task", labels=labels)
    yield task_id
    delete_task(task_id)


def test_create_and_delete_todoist_task():
    # This test purposefully doesn't use the task fixture
    task_title = "Test Task"
    task_id = create_task(task_title)
    assert task_exists(task_id)
    delete_task(task_id)
    assert not task_exists(task_id)


@pytest.mark.parametrize("labels", ["foo", "foo,bar"], indirect=True)
def test_create_todoist_task_with_label(task, labels):
    assert task_exists(task)
    assert "foo" in get_task(task).labels
    if "bar" in labels:
        assert "bar" in get_task(task).labels
    assert "test" in get_task(task).labels
