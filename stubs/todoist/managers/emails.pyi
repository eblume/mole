from .generic import Manager as Manager
from typing import Any

class EmailsManager(Manager):
    def get_or_create(self, obj_type: Any, obj_id: Any, **kwargs: Any): ...
    def disable(self, obj_type: Any, obj_id: Any, **kwargs: Any): ...
