# -*- coding: utf-8 -*-
import mole


def test_detects_tasks(store: mole.Store, tasks: list[mole.Task]):
    for task in tasks:
        assert task in store
