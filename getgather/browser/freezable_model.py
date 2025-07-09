from typing import Any

from pydantic import BaseModel, PrivateAttr


class FreezableModel(BaseModel):
    _frozen: bool = PrivateAttr(default=False)

    def freeze(self) -> None:
        """Lock this instance against any further attribute changes."""
        object.__setattr__(self, "_frozen", True)

    def __setattr__(self, name: str, value: Any):
        if getattr(self, "_frozen", False):
            raise TypeError(f"{self.__class__.__name__} is frozen; cannot set {name!r}")
        super().__setattr__(name, value)

    def __delattr__(self, name: str):
        if getattr(self, "_frozen", False):
            raise TypeError(f"{self.__class__.__name__} is frozen; cannot delete {name!r}")
        super().__delattr__(name)
