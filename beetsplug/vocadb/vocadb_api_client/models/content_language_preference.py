from beetsplug.vocadb.vocadb_api_client.models import StrEnum


class ContentLanguagePreference(StrEnum):
    ENGLISH = "English"
    JAPANESE = "Japanese"
    ROMAJI = "Romaji"
    DEFAULT = "Default"
