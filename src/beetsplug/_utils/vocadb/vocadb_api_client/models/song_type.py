from enum import auto

from . import PascalCaseStrEnum, StrEnumSet, TypeAlias


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
    DRAMAPV = auto()
    LIVE = auto()
    ILLUSTRATION = auto()
    OTHER = auto()

    # TouhouDB-specific
    REARRANGEMENT = auto()


SongTypeSet: TypeAlias = StrEnumSet[SongType]
