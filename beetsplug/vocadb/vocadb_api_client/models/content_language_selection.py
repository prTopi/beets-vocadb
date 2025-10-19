from enum import auto

from beetsplug.vocadb.vocadb_api_client.models import PascalCaseStrEnum


class ContentLanguageSelection(PascalCaseStrEnum):
    UNSPECIFIED = auto()
    JAPANESE = auto()
    ROMAJI = auto()
    ENGLISH = auto()
