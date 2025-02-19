import pytest
import os
from mole.todoist import create_task, delete_task, task_exists

pytestmark = pytest.mark.skipif(
    os.getenv("INTEGRATION_MODE") != "true", reason="Integration mode not enabled"
)


def test_create_and_delete_todoist_task():
    # Create a task using the mole.todoist module
    task_title = "Test Task"
    task_id = create_task(task_title)

    # Verify the task exists after creation
    assert task_exists(task_id)

    # Delete the task using the mole.todoist module
    delete_task(task_id)

    # Verify the task is deleted using the mole.todoist module
    assert not task_exists(task_id)
