import sqlite3
import uuid
from typing import Optional
from dataclasses import dataclass


@dataclass
class ChoreDefinition:
    name: str
    interval_days: int


class Task:
    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        completed: bool = False,
        todoist_id: Optional[int] = None,
    ):
        self.id: str = id or str(uuid.uuid4())
        self.name: Optional[str] = name
        self.completed: bool = completed
        self.todoist_id: Optional[int] = todoist_id

    @staticmethod
    def create_table(connection: sqlite3.Connection) -> None:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    completed BOOLEAN NOT NULL,
                    todoist_id INTEGER
                )
            """)

    def save(self, connection: sqlite3.Connection) -> None:
        with connection:
            connection.execute(
                """
                INSERT INTO tasks (id, name, completed, todoist_id) VALUES (?, ?, ?, ?)
            """,
                (self.id, self.name, self.completed, self.todoist_id),
            )

    @staticmethod
    def get(connection: sqlite3.Connection, task_id: str) -> Optional["Task"]:
        task = connection.execute(
            """
            SELECT id, name, completed, todoist_id FROM tasks WHERE id = ?
        """,
            (task_id,),
        ).fetchone()
        if task:
            return Task(id=task[0], name=task[1], completed=task[2], todoist_id=task[3])
        return None

    def complete(self, connection: sqlite3.Connection) -> None:
        self.completed = True
        with connection:
            connection.execute(
                """
                UPDATE tasks SET completed = ? WHERE id = ?
            """,
                (self.completed, self.id),
            )
