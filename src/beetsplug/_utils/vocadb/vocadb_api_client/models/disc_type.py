from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


class DiscType(PascalCaseStrEnum):
    UNKNOWN = auto()
    ALBUM = auto()
    SINGLE = auto()
    E_P = auto()
    SPLIT_ALBUM = auto()
    COMPILATION = auto()
    VIDEO = auto()
    ARTBOOK = auto()
    GAME = auto()
    FANMADE = auto()
    INSTRUMENTAL = auto()
    OTHER = auto()


DiscTypeSet: TypeAlias = StrEnumSet[DiscType]
