from enum import auto

from . import PascalCaseStrEnum


class TranslationType(PascalCaseStrEnum):
    ORIGINAL = auto()
    ROMANIZED = auto()
    TRANSLATION = auto()
