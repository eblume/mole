# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from dataclasses import dataclass
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

from .remote import SyncClient

if TYPE_CHECKING:
    from .engine import Engine


class ConfigError(Exception):
    pass


@dataclass
class Config:
    remote: str = "local"
    verbose: bool = False
    debug: bool = False
    api_key: str = "YOU_MUST_SET_YOUR_TODOIST_KEY"

    @classmethod
    def load_via_module(cls, path: Path) -> Config:
        # TODO - make this all less fragile, etc.
        user_spec = importlib.util.spec_from_file_location("user_spec", path)
        assert user_spec is not None
        assert user_spec.loader is not None
        config_module = importlib.util.module_from_spec(user_spec)
        user_spec.loader.exec_module(config_module)
        assert hasattr(config_module, "config")
        config = config_module.config
        assert isinstance(config, cls)
        return config

    def make_client(self, engine: Engine) -> SyncClient:
        if self.remote == "todoist":
            from .todoist import TodoistSyncClient

            return TodoistSyncClient.from_api_key(engine)
        raise NotImplementedError("Unknown remote type %s", self.remote)
