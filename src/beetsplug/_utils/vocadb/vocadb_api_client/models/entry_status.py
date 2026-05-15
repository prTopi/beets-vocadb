from enum import auto

from . import PascalCaseStrEnum


class EntryStatus(PascalCaseStrEnum):
    DRAFT = auto()
    FINISHED = auto()
    APPROVED = auto()
    LOCKED = auto()
