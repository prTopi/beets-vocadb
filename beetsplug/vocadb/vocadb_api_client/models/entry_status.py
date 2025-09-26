from beetsplug.vocadb.vocadb_api_client.models import StrEnum


class EntryStatus(StrEnum):
    DRAFT = "Draft"
    FINISHED = "Finished"
    APPROVED = "Approved"
    LOCKED = "Locked"
