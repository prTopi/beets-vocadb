from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class TranslationType(PascalCaseStrEnum):
    ORIGINAL = auto()
    ROMANIZED = auto()
    TRANSLATION = auto()
