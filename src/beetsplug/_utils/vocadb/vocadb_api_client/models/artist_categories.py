from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


class ArtistCategories(PascalCaseStrEnum):
    VOCALIST = auto()
    NOTHING = auto()
    PRODUCER = auto()
    ANIMATOR = auto()
    LABEL = auto()
    CIRCLE = auto()
    OTHER = auto()
    BAND = auto()
    ILLUSTRATOR = auto()
    SUBJECT = auto()


ArtistCategoriesSet: TypeAlias = StrEnumSet[ArtistCategories]
