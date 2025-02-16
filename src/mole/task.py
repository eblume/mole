import sqlite3
import uuid
from typing import Optional


class Task:
    def __init__(
        self,
        id: Optional[str] = None,
        name: Optional[str] = None,
        completed: bool = False,
    ):
        self.id: str = id or str(uuid.uuid4())
        self.name: Optional[str] = name
        self.completed: bool = completed

    @staticmethod
    def create_table(connection: sqlite3.Connection) -> None:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    completed BOOLEAN NOT NULL
                )
            """)

    def save(self, connection: sqlite3.Connection) -> None:
        with connection:
            connection.execute(
                """
                INSERT INTO tasks (id, name, completed) VALUES (?, ?, ?)
            """,
                (self.id, self.name, self.completed),
            )

    @staticmethod
    def get(connection: sqlite3.Connection, task_id: str) -> Optional["Task"]:
        task = connection.execute(
            """
            SELECT id, name, completed FROM tasks WHERE id = ?
        """,
            (task_id,),
        ).fetchone()
        if task:
            return Task(id=task[0], name=task[1], completed=task[2])
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
