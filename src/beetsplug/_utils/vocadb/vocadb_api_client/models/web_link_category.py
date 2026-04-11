from enum import auto

from . import PascalCaseStrEnum


class WebLinkCategory(PascalCaseStrEnum):
    OFFICIAL = auto()
    COMMERCIAL = auto()
    REFERENCE = auto()
    OTHER = auto()
