from __future__ import annotations

import sys
from typing import TypeVar

import msgspec

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


if not sys.version_info < (3, 11):
    from enum import StrEnum  # pyright: ignore[reportUnreachable]
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """
        Compatible StrEnum implementation for Python < 3.11
        """

        _value_: str

        @override
        def __new__(cls, value: str) -> StrEnum:
            obj = str.__new__(cls, value)
            obj._value_ = value
            return obj

        @override
        def __str__(self) -> str:
            return self.value


E = TypeVar("E", bound=StrEnum)


class StrEnumSet(set[E]):
    @override
    def __str__(self) -> str:
        return ",".join(self)

    @classmethod
    def from_csv(cls, strenum_cls: type[E], csv: str) -> StrEnumSet[E]:
        return cls(strenum_cls(role.strip()) for role in csv.split(","))


class TaggedBase(
    msgspec.Struct,
    forbid_unknown_fields=True,
    omit_defaults=True,
    rename="camel",
): ...


class FrozenBase(
    msgspec.Struct,
    frozen=True,
    forbid_unknown_fields=True,
    omit_defaults=True,
    rename="camel",
): ...


# Explicitly export the public API
__all__ = ["StrEnum", "StrEnumSet"]
