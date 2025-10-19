from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import (
    PascalCaseStrEnum,
    StrEnumSet,
    TypeAlias,
)


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
