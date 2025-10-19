from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class EntryStatus(PascalCaseStrEnum):
    DRAFT = auto()
    FINISHED = auto()
    APPROVED = auto()
    LOCKED = auto()
