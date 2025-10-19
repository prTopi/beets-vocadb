from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase
from beetsplug.vocadb.vocadb_api_client.models.disc_media_type import (
    DiscMediaType,
)


class AlbumDiscPropertiesContract(FrozenBase, frozen=True):
    disc_number: int
    id: int
    media_type: DiscMediaType
    name: str | None = None
