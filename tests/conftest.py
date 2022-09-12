# -*- coding: utf-8 -*-
from typing import Iterable

import pytest
from utils import FakeSyncClient

import mole


@pytest.fixture()
def client() -> mole.SyncClient:
    return FakeSyncClient()


@pytest.fixture()
def config(client: mole.SyncClient, mocker) -> mole.Config:
    config = mole.Config(debug=True, api_key="TestFakeCreds")
    mocker.patch.object(config, "make_client", lambda *_: client)
    return config


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
