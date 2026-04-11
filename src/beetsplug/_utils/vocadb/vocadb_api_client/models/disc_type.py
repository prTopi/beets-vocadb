from enum import auto

from . import PascalCaseStrEnum


class DiscType(PascalCaseStrEnum):
    UNKNOWN = auto()
    ALBUM = auto()
    SINGLE = auto()
    E_P = auto()
    SPLIT_ALBUM = auto()
    COMPILATION = auto()
    VIDEO = auto()
    ARTBOOK = auto()
    GAME = auto()
    FANMADE = auto()
    INSTRUMENTAL = auto()
    OTHER = auto()
