# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Type

from requests_toolbelt.sessions import BaseUrlSession

from .remote import Remote, RemoteConfig
from .task import Task


class MotionRequestSession(BaseUrlSession):
    def __init__(self, base_url: str, key: str, workspace_id: str):
        super().__init__(base_url)
        self.headers.update({"X-Api-Key": key})
        self._workspace_id = workspace_id

    def request(self, method, url, *args, **kwargs):
        kwargs.setdefault("params", {})
        kwargs["params"].setdefault("workspaceId", self._workspace_id)
        kwargs["params"].setdefault("label", "mole")
        return super().request(method, url, *args, **kwargs)


@dataclass
class MotionRemoteConfig(RemoteConfig):
    key: str = field(repr=False)
    workspace_id: str = field(
        default="bQVc-ObV-rpN1G8YtFUyg"
    )  # TODO remove insane personal default, lol


class MotionRemote(Remote[MotionRemoteConfig]):
    def __init__(self, config: MotionRemoteConfig):
        self.config = config

    @classmethod
    def from_config(cls: Type[MotionRemote], config: MotionRemoteConfig) -> MotionRemote:
        return MotionRemote(config)

    def get_tasks(self) -> list[Task]:
        self.log.debug("Retrieving tasks")
        response = self.session.get("tasks")
        assert response.status_code == 200
        json_tasks = response.json()
        assert len(json_tasks) > 0
        self.log.debug("Retrieved tasks: %s", json_tasks)
        tasks = []
        for json_task in json_tasks:
            completed = "Completed" in {s["name"] for s in json_task["statuses"]}
            name = json_task["name"]
            tasks.append(Task(name=name, completed=completed))
        return tasks

    def create_task(self, task: Task):
        self.log.debug("Creating task: %s", task)

    @property
    def session(self) -> MotionRequestSession:
        if not hasattr(self, "_session"):
            base_url = "https://api.usemotion.com/v1/"
            self._session = MotionRequestSession(
                base_url, self.config.key, self.config.workspace_id
            )
            assert self._session is not None
        return self._session
