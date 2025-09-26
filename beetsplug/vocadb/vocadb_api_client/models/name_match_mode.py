from beetsplug.vocadb.vocadb_api_client.models import StrEnum


class NameMatchMode(StrEnum):
    AUTO = "Auto"
    PARTIAL = "Partial"
    STARTSWITH = "StartsWith"
    EXACT = "Exact"
    WORDS = "Words"
