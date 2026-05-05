from enum import auto

from . import PascalCaseStrEnum, StrEnumSet, TypeAlias


class ArtistRelationsFields(PascalCaseStrEnum):
    NONE = auto()
    LATEST_ALBUMS = auto()
    LATEST_EVENTS = auto()
    LATEST_SONGS = auto()
    POPULAR_ALBUMS = auto()
    POPULAR_SONGS = auto()
    ALL = auto()


ArtistRelationsFieldsSet: TypeAlias = StrEnumSet[ArtistRelationsFields]
