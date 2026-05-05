from enum import auto

from . import PascalCaseStrEnum, StrEnumSet, TypeAlias


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
