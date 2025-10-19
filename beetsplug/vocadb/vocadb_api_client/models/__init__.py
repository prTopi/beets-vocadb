from __future__ import annotations

import sys
from typing import Generic, TypeVar

import msgspec

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


if not sys.version_info < (3, 11):
    from enum import StrEnum  # pyright: ignore[reportUnreachable]
else:
    from backports.strenum import StrEnum

if not sys.version_info < (3, 10):
    from typing import TypeAlias  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import TypeAlias


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


_E = TypeVar("_E", bound=StrEnum)
_E2 = TypeVar("_E2", bound=StrEnum)


class StrEnumSet(set[_E], Generic[_E]):
    _enum_cls: type[_E]

    @override
    def __str__(self) -> str:
        return ",".join(self)

    @staticmethod
    def from_delimited_str(
        strenum_cls: type[_E2], csv: str, delimiter: str = ","
    ) -> StrEnumSet[_E2]:
        return StrEnumSet[_E2](
            strenum_cls(role.strip()) for role in csv.split(delimiter)
        )


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
__all__: list[str] = ["StrEnum", "TypeAlias"]
