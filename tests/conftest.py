import sqlite3
import pytest
from mole.task import Task


@pytest.fixture
def db_connection():
    connection = sqlite3.connect(":memory:")
    Task.create_table(connection)
    yield connection
    connection.close()
