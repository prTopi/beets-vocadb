from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class WebLinkCategory(PascalCaseStrEnum):
    OFFICIAL = auto()
    COMMERCIAL = auto()
    REFERENCE = auto()
    OTHER = auto()
