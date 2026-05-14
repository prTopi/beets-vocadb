from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


class ArtistRelationsFields(PascalCaseStrEnum):
    NONE = auto()
    LATEST_ALBUMS = auto()
    LATEST_EVENTS = auto()
    LATEST_SONGS = auto()
    POPULAR_ALBUMS = auto()
    POPULAR_SONGS = auto()
    ALL = auto()


ArtistRelationsFieldsSet: TypeAlias = StrEnumSet[ArtistRelationsFields]
