import sqlite3
from typing import Optional, List
import appdirs
from datetime import datetime, timedelta
from .task import Task, ChoreDefinition


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
                last_completed_date = datetime.strptime(last_completed[0], "%Y-%m-%d")
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
