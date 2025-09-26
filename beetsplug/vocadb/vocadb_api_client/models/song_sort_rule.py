from beetsplug.vocadb.vocadb_api_client.models import StrEnum


class SongSortRule(StrEnum):
    NONE = "None"
    NAME = "Name"
    ADDITIONDATE = "AdditionDate"
    PUBLISHDATE = "PublishDate"
    FAVORITEDTIMES = "FavoritedTimes"
    RATINGSCORE = "RatingScore"
    TAGUSAGECOUNT = "TagUsageCount"
    SONGTYPE = "SongType"
