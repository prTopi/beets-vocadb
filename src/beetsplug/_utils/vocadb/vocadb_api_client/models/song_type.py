from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


class SongType(PascalCaseStrEnum):
    UNSPECIFIED = auto()
    ORIGINAL = auto()
    REMASTER = auto()
    REMIX = auto()
    COVER = auto()
    ARRANGEMENT = auto()
    INSTRUMENTAL = auto()
    MASHUP = auto()
    SHORT_VERSION = auto()
    MUSIC_P_V = auto()
    DRAMA_P_V = auto()
    LIVE = auto()
    ILLUSTRATION = auto()
    OTHER = auto()

    # TouhouDB-specific
    REARRANGEMENT = auto()


SongTypeSet: TypeAlias = StrEnumSet[SongType]
