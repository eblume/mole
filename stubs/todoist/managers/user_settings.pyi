from .generic import Manager as Manager
from typing import Any

class UserSettingsManager(Manager):
    def update(self, **kwargs: Any) -> None: ...
