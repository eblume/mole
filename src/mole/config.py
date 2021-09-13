# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path


@dataclass(frozen=True)
class Config:
    verbose: bool = False
    debug: bool = False
    api_key: str = "YOU_MUST_SET_YOUR_TODOIST_KEY"

    @classmethod
    def load_via_module(cls, path: Path) -> Config:
        user_spec = importlib.util.spec_from_file_location("user_spec", path)
        assert user_spec is not None
        config_module = importlib.util.module_from_spec(user_spec)
        config = user_spec.loader.exec_module(config_module).config  # type: ignore
        assert isinstance(config, cls)
        return config
