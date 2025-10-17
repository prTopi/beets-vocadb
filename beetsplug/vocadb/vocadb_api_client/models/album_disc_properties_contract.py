from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.disc_media_type import (
    DiscMediaType,
)


class AlbumDiscPropertiesContract(TaggedBase):
    disc_number: int
    id: int
    media_type: DiscMediaType
    name: str | None = None
    total: int | None = None  # Not provided by the API!
