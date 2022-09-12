# -*- coding: utf-8 -*-
import pytest

import mole


@pytest.fixture()
def config() -> mole.Config:
    return mole.Config(debug=True, api_key="TestFakeCreds")


@pytest.fixture()
def engine(config: mole.Config) -> mole.Engine:
    return config.make_engine()


@pytest.fixture()
def store(engine: mole.Engine) -> mole.Store:
    return engine.store


@pytest.fixture()
def tasks(store: mole.Store) -> list[mole.Task]:
    tasks = [
        mole.Task("Test Task 1"),
        mole.Task("Test Task 2"),
        mole.Task("Test Task 3"),
    ]

    for task in tasks:
        store.add_task(task)

    return tasks
