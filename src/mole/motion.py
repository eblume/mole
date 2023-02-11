# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Type

from requests_toolbelt.sessions import BaseUrlSession

from .remote import Remote, RemoteConfig
from .task import Task


class MotionRequestSession(BaseUrlSession):
    def __init__(self, base_url: str, key: str, workspace_id: str):
        super().__init__(base_url)
        self.headers.update({"X-Api-Key": key})
        self.workspace_id = workspace_id

    def request(self, method, url, *args, **kwargs):
        kwargs.setdefault("params", {})
        kwargs["params"].setdefault("workspaceId", self.workspace_id)
        kwargs["params"].setdefault("label", "mole")
        return super().request(method, url, *args, **kwargs)


@dataclass
class MotionRemoteConfig(RemoteConfig):
    key: str = field(repr=False)
    workspace_id: str = field(
        default="bQVc-ObV-rpN1G8YtFUyg"
    )  # TODO remove insane personal default, lol


class MotionRemote(Remote[MotionRemoteConfig]):
    def get_tasks(self, name: Optional[str] = None) -> list[Task]:
        self.log.debug("Retrieving tasks")

        params = {}
        if name is not None:
            params["name"] = name

        response = self.session.get("tasks", params=params)
        assert response.status_code == 200

        json_tasks = response.json()
        self.log.debug("Retrieved tasks: %s", json_tasks)

        tasks = []
        for json_task in json_tasks:
            completed = json_task.get("completed", False)
            tasks.append(Task(name=json_task["name"], completed=completed))
        return tasks

    def create_task(self, task: Task):
        self.log.debug("Creating task: %s", task)
        response = self.session.post(
            "tasks",
            json={
                "duration": "REMINDER",
                "autoScheduled": {
                    "deadlineType": "NONE",
                    "schedule": "Work Hours",
                },
                "name": "Whack-a-Mole",
                "workspaceId": self.session.workspace_id,
                "labels": ["mole"],
            },
        )
        # TODO better error detection
        assert 200 <= response.status_code < 400

    @property
    def session(self) -> MotionRequestSession:
        if not hasattr(self, "_session"):
            base_url = "https://api.usemotion.com/v1/"
            self._session = MotionRequestSession(
                base_url, self.config.key, self.config.workspace_id
            )
            assert self._session is not None
        return self._session
