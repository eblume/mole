# -*- coding: utf-8 -*-
"""Bespoke todoist async-sync client with local queries.

"Async-sync" means that the client is asynchronous via asyncio, but uses the Todoist Sync API:
https://developer.todoist.com/sync/v9

Why not use doist's todoist-python? It's deprecated and abandoned.

Why not use doist's todoist-api-python? It doesn't use the sync API and is therefore inefficient for
some access patterns. Also it's a hilarious misuse of 'async'.

The core idea of this client is to provide an infinite async loop that synchronizes with the Todoist
API servers, and emits events relevant sync events.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import datetime as dt
from enum import Enum
import logging
from typing import Any, Iterable, List, TYPE_CHECKING

import requests

from mole.models import Task

from .remote import SyncClient
from .store import Store, StoreUpdater

if TYPE_CHECKING:
    from .engine import Engine


class Resources(Enum):
    _all = "all"
    labels = "labels"
    projects = "projects"
    items = "items"
    notes = "notes"
    sections = "sections"
    filters = "filters"
    reminders = "reminders"
    locations = "locations"
    user = "user"
    live_notifications = "live_notifications"
    collaborators = "collaborators"
    user_settings = "user_settings"
    notification_settings = "notification_settings"
    user_plan_limits = "user_plan_limits"
    completed_info = "completed_info"
    stats = "stats"


@dataclass
class TodoistSyncClient(SyncClient):
    engine: Engine
    api: TodoistAPI
    sync_period: dt.timedelta = dt.timedelta(minutes=5)

    @classmethod
    def from_oauth(cls) -> TodoistSyncClient:
        raise NotImplementedError("Not implemented (yet)")  # TODO

    @classmethod
    def from_api_key(cls, engine: Engine) -> TodoistSyncClient:
        """Use a developer API key to create a TodoistAPI client connection.

        The API key will be retrieved from `engine.config.api_key`.
        """
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {engine.config.api_key}"})
        api = TodoistAPI(store=engine.store, session=session)
        client = TodoistSyncClient(engine=engine, api=api)
        if client.engine.config.debug:
            client.log.debug("Debug synchronization mode: sync_period set to 10 seconds")
            client.sync_period = dt.timedelta(seconds=10)
        return client

    async def run(self):
        """Run 'forever', periodically polling the synchronization API"""
        # NB: In the future, I may want to allow for a shutdown event. But for now, I'm letting
        # the KeyboardInterrupt from a ctrl+c be that shutdown event.
        while True:
            await self.api.synchronize()
            await asyncio.sleep(self.sync_period.total_seconds())


@dataclass
class TodoistAPI:
    store: Store
    session: requests.Session
    base_url: str = "https://api.todoist.com/sync/v9/sync"
    sync_token: str = "*"

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    async def synchronize(self, resources: List[Resources] = [Resources._all]) -> None:
        # requested_resources is a STRING (not array!!) with a special format, eg.: '["labels", "projects"]'
        if Resources._all in resources:
            # if resources contains Resources._all, it's a special case and all other resource types are ignored.
            requested_resources = '["all"]'
        else:
            quoted_resources = ",".join(f'"{r.value}"' for r in resources)
            requested_resources = f"[{quoted_resources}]"

        payload = {
            "sync_token": self.sync_token,
            "resource_types": requested_resources,
        }

        self.log.info("Sending new sync request for token %s", self.sync_token)
        # TODO - move to aiohttp or some other asyncio-compatible request library, so we don't block everything here
        # (this is crucial or else we may as well have been non-async...)
        response = self.session.post(self.base_url, json=payload)
        response.raise_for_status()
        data = response.json()
        self.log.debug("Sync request response received")
        self.log.debug(data)

        # Update the next sync token
        self.sync_token = data["sync_token"]

        # Create a StoreUpdate from this data
        update = TodoistUpdater(data)
        await self.store.update(update)


@dataclass
class TodoistUpdater(StoreUpdater):
    data: dict[str, Any]

    def new_tasks(self) -> Iterable[Task]:
        for item in self.data.get("items", []):
            yield Task(name=item["content"])

    def should_clear(self) -> bool:
        return self.data.get("full_sync", False)
