from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

from . import PascalCaseStrEnum, StrEnumSet

if TYPE_CHECKING:
    from . import TypeAlias


class TagOptionalFields(PascalCaseStrEnum):
    NONE = auto()
    ADDITIONAL_NAMES = auto()
    ALIASED_TO = auto()
    DESCRIPTION = auto()
    MAIN_PICTURE = auto()
    NAMES = auto()
    PARENT = auto()
    RELATED_TAGS = auto()
    TRANSLATED_DESCRIPTION = auto()
    WEBLINKS = auto()


TagOptionalFieldsSet: TypeAlias = StrEnumSet[TagOptionalFields]
