# -*- coding: utf-8 -*-
from mole import SyncClient


class FakeSyncClient(SyncClient):
    async def run(self) -> None:
        return
