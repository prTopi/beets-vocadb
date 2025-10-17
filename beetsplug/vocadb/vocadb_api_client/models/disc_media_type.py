from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class DiscMediaType(PascalCaseStrEnum):
    AUDIO = auto()
    VIDEO = auto()
