import sqlite3
import uuid
from typing import Optional, List
import appdirs
from datetime import datetime, timedelta
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

    @staticmethod
    def update_chores(
        connection: Optional[sqlite3.Connection] = None,
        chore_definitions: List[ChoreDefinition] = [],
    ):
        if connection is None:
            db_path = appdirs.user_cache_dir("mole", "") + "/task.db"
            connection = sqlite3.connect(db_path)

        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS chore_completions (
                    chore_name TEXT PRIMARY KEY,
                    last_completed DATE
                )
            """)

            for chore in chore_definitions:
                name = chore.name
                interval_days = chore.interval_days
                last_completed = connection.execute(
                    "SELECT last_completed FROM chore_completions WHERE chore_name = ?",
                    (name,),
                ).fetchone()

                if last_completed:
                    last_completed_date = datetime.strptime(
                        last_completed[0], "%Y-%m-%d"
                    )
                    if datetime.now() - last_completed_date >= timedelta(
                        days=interval_days
                    ):
                        Task(name=name).save(connection)
                        connection.execute(
                            "UPDATE chore_completions SET last_completed = DATE('now') WHERE chore_name = ?",
                            (name,),
                        )
                else:
                    Task(name=name).save(connection)
                    connection.execute(
                        "INSERT INTO chore_completions (chore_name, last_completed) VALUES (?, DATE('now'))",
                        (name,),
                    )
