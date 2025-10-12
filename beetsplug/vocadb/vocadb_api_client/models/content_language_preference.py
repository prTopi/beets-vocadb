from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class ContentLanguagePreference(PascalCaseStrEnum):
    ENGLISH = auto()
    JAPANESE = auto()
    ROMAJI = auto()
    DEFAULT = auto()
