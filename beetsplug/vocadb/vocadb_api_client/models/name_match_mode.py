from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class NameMatchMode(PascalCaseStrEnum):
    AUTO = auto()
    PARTIAL = auto()
    STARTS_WITH = auto()
    EXACT = auto()
    WORDS = auto()
