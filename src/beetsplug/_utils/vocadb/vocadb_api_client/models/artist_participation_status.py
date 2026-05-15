from enum import auto

from . import PascalCaseStrEnum


class ArtistParticipationStatus(PascalCaseStrEnum):
    EVERYTHING = auto()
    ONLYMAINALBUMS = auto()
    ONLYCOLLABORATIONS = auto()
