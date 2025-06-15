import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path

import appdirs
import pendulum
from sqlite_utils.db import Database, Table


COMPLETIONS_TABLE = "chore_completions"


@dataclass
class ChoreDefinition:
    name: str
    interval_days: int


@dataclass
class ChoreState:
    db: Database
    chore_definitions: list[ChoreDefinition] = field(default_factory=list)

    @classmethod
    def from_sqlite_file(
        cls, path: Path = Path(appdirs.user_cache_dir("mole", "")) / "task.db"
    ):
        return cls(db=Database(path))

    @classmethod
    def from_volatile_memory(cls):
        return cls(db=Database(memory=True))

    @property
    def due_chores(self) -> list[ChoreDefinition]:
        return [
            chore for chore in self.chore_definitions if chore_is_due(self.db, chore)
        ]

    def __post_init__(self) -> None:
        table = get_table(self.db, COMPLETIONS_TABLE)
        table.create(
            {
                "name": str,
                "completed_at": dt.datetime,
            }
        )

    def mark_complete(self, name: str) -> None:
        table = get_table(self.db, COMPLETIONS_TABLE)
        table.insert({"name": name, "completed_at": pendulum.now()})


def chore_is_due(db: Database, chore: ChoreDefinition) -> bool:
    cursor = db.execute(
        f"select completed_at from {COMPLETIONS_TABLE} where name = ? order by completed_at limit 1",
        [chore.name],
    )
    row = cursor.fetchone()
    if row is None:
        return True
    when = pendulum.parse(row[0])
    assert isinstance(when, pendulum.DateTime)
    now = pendulum.now()
    diff = when.diff(now)
    return diff.in_days() >= chore.interval_days


def get_table(db: Database, name: str) -> Table:
    """Retrieve a Table, never a view, type safe"""
    table = db[name]
    assert isinstance(table, Table)
    return table
