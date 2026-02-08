from __future__ import annotations

from datetime import datetime

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase
from beetsplug.vocadb.vocadb_api_client.models.artist_type import ArtistType
from beetsplug.vocadb.vocadb_api_client.models.entry_status import EntryStatus


class ArtistContract(FrozenBase, frozen=True):
    artist_type: ArtistType
    deleted: bool
    id: int
    status: EntryStatus
    version: int
    additional_names: str | None = None
    name: str | None = None
    release_date: datetime | None = None
    picture_mime: str | None = None
