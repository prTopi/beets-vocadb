from enum import auto

from . import PascalCaseStrEnum


class TagSortRule(PascalCaseStrEnum):
    NOTHING = auto()
    NAME = auto()
    ADDITIONDATE = auto()
    USAGECOUNT = auto()
