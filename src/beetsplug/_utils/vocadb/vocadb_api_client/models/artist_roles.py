from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


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
    RECORDING_ENGINEER = auto()


ArtistRolesSet: TypeAlias = StrEnumSet[ArtistRoles]
