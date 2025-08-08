from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from getgather.database.repositories.activity_repository import Activity

current_activity: ContextVar["Activity | None"] = ContextVar('current_activity', default=None)