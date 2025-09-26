import sys

from beetsplug.vocadb.vocadb_api_client.models import StrEnum, StrEnumSet

if not sys.version_info < (3, 10):
    from typing import TypeAlias  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import TypeAlias


class AlbumSortRule(StrEnum):
    NONE = "None"
    NAME = "Name"
    RELEASEDATE = "ReleaseDate"
    RELEASEDATEWITHNULLS = "ReleaseDateWithNulls"
    ADDITIONDATE = "AdditionDate"
    RATINGAVERAGE = "RatingAverage"
    RATINGTOTAL = "RatingTotal"
    NAMETHENRELEASEDATE = "NameThenReleaseDate"
    COLLECTIONCOUNT = "CollectionCount"


AlbumSortRuleSet: TypeAlias = StrEnumSet[AlbumSortRule]
