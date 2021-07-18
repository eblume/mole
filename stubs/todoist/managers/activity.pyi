from .generic import Manager as Manager
from typing import Any

class ActivityManager(Manager):
    def get(self, **kwargs: Any): ...
