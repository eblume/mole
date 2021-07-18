from .. import models as models
from .generic import AllMixin as AllMixin, GetByIdMixin as GetByIdMixin, Manager as Manager, SyncMixin as SyncMixin
from typing import Any, Optional

class ItemsManager(Manager, AllMixin, GetByIdMixin, SyncMixin):
    state_name: str = ...
    object_type: str = ...
    def add(self, content: Any, **kwargs: Any): ...
    def update(self, item_id: Any, **kwargs: Any) -> None: ...
    def delete(self, item_id: Any) -> None: ...
    def move(self, item_id: Any, **kwargs: Any) -> None: ...
    def close(self, item_id: Any) -> None: ...
    def complete(self, item_id: Any, date_completed: Optional[Any] = ..., force_history: Optional[Any] = ...) -> None: ...
    def uncomplete(self, item_id: Any) -> None: ...
    def archive(self, item_id: Any) -> None: ...
    def unarchive(self, item_id: Any) -> None: ...
    def update_date_complete(self, item_id: Any, due: Optional[Any] = ...) -> None: ...
    def reorder(self, items: Any) -> None: ...
    def update_day_orders(self, ids_to_orders: Any) -> None: ...
    def get_completed(self, project_id: Any, **kwargs: Any): ...
    def get(self, item_id: Any): ...
