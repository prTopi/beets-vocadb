from enum import auto

from . import PascalCaseStrEnum


class ContentLanguagePreference(PascalCaseStrEnum):
    ENGLISH = auto()
    JAPANESE = auto()
    ROMAJI = auto()
    DEFAULT = auto()
