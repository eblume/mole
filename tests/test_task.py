import sqlite3
import pytest
from mole.task import Task

@pytest.fixture
def db_connection():
    connection = sqlite3.connect(':memory:')
    Task.create_table(connection)
    yield connection
    connection.close()


def test_create_and_complete_task(db_connection):
    # Create a new task
    task = Task()
    task.save(db_connection)

    # Retrieve the task and check its initial state
    retrieved_task = Task.get(db_connection, task.id)
    assert retrieved_task is not None
    assert not retrieved_task.completed

    # Complete the task
    retrieved_task.complete(db_connection)

    # Retrieve the task again and check its state
    completed_task = Task.get(db_connection, task.id)
    assert completed_task.completed 