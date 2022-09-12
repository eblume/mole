# -*- coding: utf-8 -*-
import mole


def test_detects_tasks(store: mole.Store, tasks: list[mole.Task]):
    for task in tasks:
        assert task in store


def test_config_can_make_engine(config: mole.Config):
    engine = config.make_engine()
    assert isinstance(engine, mole.Engine)


def test_config_can_make_client(config: mole.Config, engine: mole.Engine):
    client = config.make_client(engine)
    assert isinstance(client, mole.SyncClient)


def test_client_is_fake(client: mole.SyncClient):
    from utils import FakeSyncClient

    assert isinstance(client, FakeSyncClient)
