from enum import auto

from . import PascalCaseStrEnum, StrEnumSet, TypeAlias


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
