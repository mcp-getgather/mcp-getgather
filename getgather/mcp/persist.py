import threading
from pathlib import Path
from typing import Any, Generic, Literal, Self, TypeVar, overload

from pydantic import BaseModel, PrivateAttr, model_validator

from getgather.config import settings

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
    _indexes: dict[str, int] = PrivateAttr(default={})  # key -> row_number
    _lock: threading.RLock = PrivateAttr(default_factory=lambda: threading.RLock())

    rows: list[T] = []

    @model_validator(mode="after")
    def validate_key(self) -> Self:
        assert self._key_field in self._row_model.model_fields
        return self

    @property
    def file_path(self) -> Path:
        return settings.persistent_store_dir / self._file_name

    def key_for_retrieval(self, model_key: str) -> Any:
        return model_key

    def row_key_for_retrieval(self, row: T) -> Any:
        return self.key_for_retrieval(getattr(row, self._key_field))

    def row_key_for_index(self, row: T) -> Any:
        return getattr(row, self._key_field)

    def load(self):
        with self._lock:
            if not self.file_path.exists():
                return

            with open(self.file_path, "r") as f:
                data = self.model_validate_json(f.read())
                self.rows = data.rows
                self._indexes = {
                    self.row_key_for_index(row): num for num, row in enumerate(self.rows)
                }

    def save(self) -> None:
        with self._lock:
            with open(self.file_path, "w") as f:
                f.write(self.model_dump_json())

    @overload
    def get(self, key: str) -> T | None: ...
    @overload
    def get(self, key: str, *, raise_on_missing: Literal[True]) -> T: ...

    def get(self, key: str, *, raise_on_missing: bool = False) -> T | None:
        with self._lock:
            if not self._indexes:
                self.load()
            row_key = self.key_for_retrieval(key)
            if row_key in self._indexes:
                num = self._indexes[row_key]
                return self.rows[num]
            elif raise_on_missing:
                raise ValueError(f"Row with key {key} not found")
            else:
                return None

    def add(self, row: T) -> T:
        with self._lock:
            if not self._indexes:
                self.load()

            key = self.row_key_for_retrieval(row)
            if key in self._indexes:
                raise ValueError(f"Row with key {key} already exists")

            self._indexes[key] = len(self.rows)
            self.rows.append(row)
            self.save()

            return row

    def update(self, row: T) -> T:
        with self._lock:
            if not self._indexes:
                self.load()

            key = self.row_key_for_retrieval(row)
            if key not in self._indexes:
                raise ValueError(f"Row with key {key} not found")

            num = self._indexes[key]
            self.rows[num] = row
            self.save()

            return row

    def get_all(self) -> list[T]:
        with self._lock:
            self.load()
            return self.rows

    def reset(self) -> None:
        with self._lock:
            self._indexes = {}
            self.rows = []
