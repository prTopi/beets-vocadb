import sys
from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import (
    PascalCaseStrEnum,
    StrEnumSet,
)

if not sys.version_info < (3, 10):
    from typing import TypeAlias  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import TypeAlias


class AlbumSortRule(PascalCaseStrEnum):
    NONE = auto()
    NAME = auto()
    RELEASE_DATE = auto()
    RELEASE_DATE_WITH_NULLS = auto()
    ADDITION_DATE = auto()
    RATING_AVERAGE = auto()
    RATING_TOTAL = auto()
    NAME_THEN_RELEASE_DATE = auto()
    COLLECTION_COUNT = auto()


AlbumSortRuleSet: TypeAlias = StrEnumSet[AlbumSortRule]
