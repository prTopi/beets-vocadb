from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import (
    PascalCaseStrEnum,
    StrEnumSet,
    TypeAlias,
)


class SongOptionalFields(PascalCaseStrEnum):
    NONE = auto()
    ADDIATIONAL_NAMES = auto()
    ALBUMS = auto()
    ARTISTS = auto()
    LYRICS = auto()
    MAIN_PICTURE = auto()
    NAMES = auto()
    P_VS = auto()
    RELEASE_EVENT = auto()
    TAGS = auto()
    THUMB_URL = auto()
    WEB_LINKS = auto()
    BPM = auto()
    CULTURE_CODES = auto()


SongOptionalFieldsSet: TypeAlias = StrEnumSet[SongOptionalFields]
