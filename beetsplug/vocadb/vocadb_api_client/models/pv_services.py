from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import (
    PascalCaseStrEnum,
    StrEnumSet,
    TypeAlias,
)


class PVServices(PascalCaseStrEnum):
    NOTHING = auto()
    NICO_NICO_DOUGA = auto()
    YOUTUBE = auto()
    SOUND_CLOUD = auto()
    VIMEO = auto()
    PIAPRO = auto()
    BILIBILI = auto()
    FILE = auto()
    LOCAL_FILE = auto()
    CREOFUGA = auto()
    BANDCAMP = auto()


PVServicesSet: TypeAlias = StrEnumSet[PVServices]
