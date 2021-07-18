from .generic import Manager as Manager
from typing import Any

class QuickManager(Manager):
    def add(self, text: Any, **kwargs: Any): ...
