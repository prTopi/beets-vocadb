from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import (
    PascalCaseStrEnum,
    StrEnumSet,
    TypeAlias,
)


class ArtistRoles(PascalCaseStrEnum):
    DEFAULT = auto()
    ANIMATOR = auto()
    ARRANGER = auto()
    COMPOSER = auto()
    DISTRIBUTOR = auto()
    ILLUSTRATOR = auto()
    INSTRUMENTALIST = auto()
    LYRICIST = auto()
    MASTERING = auto()
    MIXER = auto()
    OTHER = auto()
    PUBLISHER = auto()
    VOCAL_DATA_PROVIDER = auto()
    VOCALIST = auto()
    VOICE_MANIPULATOR = auto()

    # UtaiteDB- and TouhouDB-specific
    CHORUS = auto()

    # UtaiteDB-specific
    ENCODER = auto()


ArtistRolesSet: TypeAlias = StrEnumSet[ArtistRoles]
