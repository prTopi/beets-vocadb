from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


class AlbumOptionalFields(PascalCaseStrEnum):
    NONE = auto()
    ADDITIONAL_NAMES = auto()
    ARTISTS = auto()
    DESCRIPTION = auto()
    DISCS = auto()
    IDENTIFIERS = auto()
    MAIN_PICTURE = auto()
    NAMES = auto()
    P_VS = auto()
    RELEASE_EVENT = auto()
    TAGS = auto()
    TRACKS = auto()
    WEB_LINKS = auto()


AlbumOptionalFieldsSet: TypeAlias = StrEnumSet[AlbumOptionalFields]
