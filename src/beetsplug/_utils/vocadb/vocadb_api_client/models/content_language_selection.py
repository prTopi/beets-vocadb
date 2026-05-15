from enum import auto

from . import PascalCaseStrEnum


class ContentLanguageSelection(PascalCaseStrEnum):
    UNSPECIFIED = auto()
    JAPANESE = auto()
    ROMAJI = auto()
    ENGLISH = auto()
