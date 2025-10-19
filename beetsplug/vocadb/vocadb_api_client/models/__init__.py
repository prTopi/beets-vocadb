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
    from backports.strenum import StrEnum


class PascalCaseStrEnum(StrEnum):
    """
    StrEnum where auto() returns the PascalCase version of the member name
    """

    @override
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: list[str]
    ) -> str:
        """
        Return the PascalCase version of the member name.
        """
        return "".join(word.capitalize() for word in name.split("_"))


E = TypeVar("E", bound=StrEnum)


class StrEnumSet(set[E]):
    @override
    def __str__(self) -> str:
        return ",".join(self)

    @classmethod
    def from_delimited_str(
        cls, strenum_cls: type[E], csv: str, delimiter: str = ","
    ) -> StrEnumSet[E]:
        return cls(strenum_cls(role.strip()) for role in csv.split(delimiter))


class FrozenBase(
    msgspec.Struct,
    forbid_unknown_fields=True,
    frozen=True,
    omit_defaults=True,
    rename="camel",
): ...


class TaggedBase(
    msgspec.Struct,
    forbid_unknown_fields=True,
    omit_defaults=True,
    rename="camel",
):
    """Base for unhashable Structs"""


# Explicitly export the public API
__all__ = ["StrEnum"]
