from enum import auto

from . import PascalCaseStrEnum


class ArtistLinkType(PascalCaseStrEnum):
    CHARACTER_DESIGNER = auto()
    GROUP = auto()
    ILLUSTRATOR = auto()
    MANAGER = auto()
    VOICE_PROVIDER = auto()
