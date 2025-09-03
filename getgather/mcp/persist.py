import threading
from pathlib import Path
from typing import Any, Generic, Self, TypeVar

from pydantic import BaseModel, PrivateAttr, model_validator

from getgather.config import settings
from getgather.mcp.auth import get_auth_user

T = TypeVar("T", bound=BaseModel)


class SingletonMeta(type):
    _instances: dict[str, "SingletonMeta"] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> "SingletonMeta":
        name = cls.__name__
        if name not in cls._instances:
            cls._instances[name] = super().__call__(*args, **kwargs)
        return cls._instances[name]


class SingletonBaseModelMeta(SingletonMeta, type(BaseModel)):
    pass


class PersistentStore(BaseModel, Generic[T], metaclass=SingletonBaseModelMeta):
    _row_model: type[T] = PrivateAttr()
    _file_name: str = PrivateAttr()
    _key_field: str = PrivateAttr()
    _indexes: dict[str, tuple[int, T]] = PrivateAttr(default={})  # key -> (row_number, row)
    _lock: threading.RLock = PrivateAttr(default_factory=lambda: threading.RLock())

    rows: list[T] = []

    @model_validator(mode="after")
    def validate_key(self) -> Self:
        assert self._key_field in self._row_model.model_fields
        return self

    @property
    def file_path(self) -> Path:
        return settings.persistent_store_dir / self._file_name

    def index_key(self, model_key: str) -> Any:
        """Convert a model key to the key used to index the row."""
        return model_key

    def row_index_key(self, row: T) -> Any:
        return self.index_key(getattr(row, self._key_field))

    def load(self):
        with self._lock:
            if not self.file_path.exists():
                return

            with open(self.file_path, "r") as f:
                data = self.model_validate_json(f.read())
                self.rows = data.rows
                self._indexes = {
                    self.row_index_key(row): (index, row) for index, row in enumerate(self.rows)
                }

    def save(self) -> None:
        with self._lock:
            with open(self.file_path, "w") as f:
                f.write(self.model_dump_json())

    def get(self, key: str) -> T | None:
        if not self._indexes:
            self.load()
        row_key = self.index_key(key)
        return self._indexes[row_key][1] if row_key in self._indexes else None

    def add(self, row: T) -> T:
        if not self._indexes:
            self.load()

        key = self.row_index_key(row)
        if key in self._indexes:
            raise ValueError(f"Row with key {key} already exists")

        self._indexes[key] = (len(self.rows), row)
        self.rows.append(row)
        self.save()

        return row

    def update(self, row: T) -> T:
        if not self._indexes:
            self.load()

        key = self.row_index_key(row)
        if key not in self._indexes:
            raise ValueError(f"Row with key {key} not found")

        row_number = self._indexes[key][0]
        self._indexes[key] = (row_number, row)
        self.rows[row_number] = row
        self.save()

        return row

    def get_all(self) -> list[T]:
        self.load()
        return self.rows

    def reset(self) -> None:
        self._indexes = {}
        self.rows = []


class ModelWithAuth(BaseModel):
    user_login: str


TModelWithAuth = TypeVar("TModelWithAuth", bound=ModelWithAuth)


class PersistentStoreWithAuth(PersistentStore[TModelWithAuth]):
    """
    PersistentStore that requires user_login field in the row model.
    Rows are indexed by (user_login, _key_field).
    """

    @model_validator(mode="after")
    def validate_auth(self) -> Self:
        assert "user_login" in self._row_model.model_fields
        return self

    def index_key(self, model_key: str) -> tuple[str, str]:
        # keyed by (user_login, _key_field)
        return (get_auth_user().login, model_key)

    def get_all(self) -> list[TModelWithAuth]:
        rows = super().get_all()
        user_login = get_auth_user().login
        return list(filter(lambda a: a.user_login == user_login, rows))
