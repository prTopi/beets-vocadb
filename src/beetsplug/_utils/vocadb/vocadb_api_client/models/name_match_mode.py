from enum import auto

from . import PascalCaseStrEnum


class NameMatchMode(PascalCaseStrEnum):
    AUTO = auto()
    PARTIAL = auto()
    STARTS_WITH = auto()
    EXACT = auto()
    WORDS = auto()
