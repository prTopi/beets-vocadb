from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


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
