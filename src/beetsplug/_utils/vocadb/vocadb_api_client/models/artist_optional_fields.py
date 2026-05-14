from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


class ArtistOptionalFields(PascalCaseStrEnum):
    NONE = auto()
    ADDITIONAL_NAMES = auto()
    ARTIST_LINKS = auto()
    ARTIST_LINKS_REVERSE = auto()
    BASE_VOICEBANK = auto()
    DESCRIPTION = auto()
    MAIN_PICTURE = auto()
    NAMES = auto()
    TAGS = auto()
    WEB_LINKS = auto()


ArtistOptionalFieldsSet: TypeAlias = StrEnumSet[ArtistOptionalFields]
