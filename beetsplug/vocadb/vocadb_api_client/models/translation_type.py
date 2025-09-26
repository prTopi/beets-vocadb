from beetsplug.vocadb.vocadb_api_client.models import StrEnum


class TranslationType(StrEnum):
    ORIGINAL = "Original"
    ROMANIZED = "Romanized"
    TRANSLATION = "Translation"
