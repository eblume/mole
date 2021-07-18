# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import IO, Optional

import appdirs


@dataclass(frozen=True)
class Config:
    verbose: bool = False
    debug: bool = False
    api_key: str = "YOU_MUST_SET_YOUR_TODOIST_KEY"

    # Globals

    APP_NAME = "mole"  # TODO - finalize this before releasing.
    APP_AUTHOR = "eblume"  # TODO - finalize this before releasing.

    def write_to(self, handle: IO[bytes]):
        handle.write(self.serialize())

    def serialize(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf8")

    @classmethod
    def read_from(cls, handle: IO[bytes]) -> Config:
        data = handle.read()
        assert data is not None, "Configuration data was corrupted"  # Unclear
        data = data.strip()
        assert len(data) > 0, "Configuration data was empty"
        return cls.read_from_bytes(data)

    @classmethod
    def read_from_bytes(cls, data: bytes) -> Config:
        return cls(**json.loads(data))

    @classmethod
    def load_via_env(cls, settings_path: Optional[Path] = None) -> Config:
        if settings_path is None:
            settings_path = (
                Path(appdirs.user_config_dir(cls.APP_NAME, cls.APP_AUTHOR)) / "config.json"
            )

        if settings_path.exists():
            return cls.read_from(settings_path.open("rb"))
        else:
            return cls()  # TODO this will always fail in reality, consider if we want this
