from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


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
