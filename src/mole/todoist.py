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
from dataclasses import dataclass, field
import datetime as dt
from enum import Enum
import logging
from typing import List, Optional, Set

import requests


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
class TodoistAPI:
    session: requests.Session
    sync_tasks: Set[asyncio.Task] = field(default_factory=set)
    base_url: str = "https://api.todoist.com/sync/v9/sync"
    sync_period: dt.timedelta = dt.timedelta(minutes=5)
    sync_token: str = "*"
    debug: bool = False
    sync_lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def log(self) -> logging.Logger:
        return logging.getLogger(self.__class__.__name__)

    @classmethod
    def from_oauth(cls) -> TodoistAPI:
        """Use OAuth to create a TodoistAPI client connection."""
        raise NotImplementedError("Not implemented (yet)")  # TODO

    @classmethod
    def from_api_key(cls, key: str) -> TodoistAPI:
        """Use a developer API token to create a TodoistAPI client connection."""
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {key}"})
        return TodoistAPI(session=session)

    async def start(self) -> None:
        """(Re)Start synchronizing with the todoist API servers via asyncio.Task"""
        if self.sync_tasks:
            return
        self.log.debug("Starting new synchronization loop")
        task = asyncio.create_task(self.do_sync())
        self.sync_tasks.add(task)
        task.add_done_callback(self.sync_tasks.discard)
        await task

    async def stop(self) -> None:
        if not self.sync_tasks:
            return
        self.log.debug("Stopping synchronization loop")
        for task in self.sync_tasks:
            task.cancel()
        await asyncio.gather(*self.sync_tasks)

    async def do_sync(self) -> None:
        """Async loop handler for synchronization.

        This coroutine calls the synchronize method with Resources._all, and then
        schedules the next synchronization.
        """
        if self.debug:
            self.log.debug("Debug synchronization mode: sync_period set to 10 seconds")
            self.sync_period = dt.timedelta(seconds=10)

        while True:
            # Wait on the lock for up to sync_period / 2
            await self.synchronize(
                timeout=dt.timedelta(seconds=self.sync_period.total_seconds() / 2)
            )
            # Sleep for sync_period
            await asyncio.sleep(self.sync_period.total_seconds())

    async def synchronize(
        self, resources: List[Resources] = [Resources._all], timeout: Optional[dt.timedelta] = None
    ) -> None:
        # NB: If we passed in (and returned) a token we could in theory make this concurrent, but I think a better model
        # is to have one single 'thread' of synhronization... this means that the `resources` argument is not currently
        # very useful, though. Someday I might look in to concurrent sync strategies if eg. a UI really wants to refresh
        # just one kind of resource *right now*. Some issues: how to handle sync failures? Commits? Events? State?
        if timeout is None:
            await self.sync_lock.acquire()
        else:
            try:
                await asyncio.wait_for(self.sync_lock.acquire(), timeout.total_seconds())
            except asyncio.TimeoutError:
                self.log.warn(
                    "API synchronization lock timeout, has the synchronization thread frozen?"
                )
                return

        # requested_resources is a STRING (not array!!) with a special format, eg.: '["labels", "projects"]'
        if Resources._all in resources:
            # if resources contains Resources._all, it's a special case and all other resource types are ignored.
            requested_resources = '["all"]'
        else:
            quoted_resources = ",".join(f'"{r.value}"' for r in resources)
            requested_resources = f"[{quoted_resources}]"

        # Guarded by self.sync_lock via above:
        try:
            payload = {
                "sync_token": self.sync_token,
                "resource_types": requested_resources,
            }
            self.log.debug("Sending new sync request for token %s", self.sync_token)
            response = self.session.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.log.debug("Sync request response received")

            # Update the next sync token
            self.sync_token = data["sync_token"]

            # TODO - actually handle the response, correctly
            for item in data["items"]:
                self.log.debug("Item synchronized: %s", item["content"])

        finally:
            self.sync_lock.release()
