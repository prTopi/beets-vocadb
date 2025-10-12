from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class SongSortRule(PascalCaseStrEnum):
    NONE = auto()
    NAME = auto()
    ADDITION_DATE = auto()
    PUBLISH_DATE = auto()
    FAVORITED_TIMES = auto()
    RATING_SCORE = auto()
    TAG_USAGE_COUNT = auto()
    SONG_TYPE = auto()
