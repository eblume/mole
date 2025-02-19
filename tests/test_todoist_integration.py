import pytest
import os
from mole.todoist import create_task, delete_task, task_exists, get_task
from mole.task import Task

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


def test_create_and_link_task_with_todoist(db_connection):
    # Create a new Todoist task
    task_title = "Linked Test Task"
    todoist_task_id = create_task(task_title)
    assert task_exists(todoist_task_id)

    # Create a new Task and link it with the Todoist task
    task = Task(name=task_title, todoist_id=todoist_task_id)
    task.save(db_connection)

    # Retrieve the task and verify the link
    retrieved_task = Task.get(db_connection, task.id)
    assert retrieved_task is not None
    assert retrieved_task.name == task_title
    assert retrieved_task.todoist_id == todoist_task_id
    assert retrieved_task.todoist_id is not None  # Ensure todoist_id is not None

    # Verify the existence of the Todoist task
    assert task_exists(retrieved_task.todoist_id)

    # Clean up by deleting the Todoist task
    delete_task(todoist_task_id)
