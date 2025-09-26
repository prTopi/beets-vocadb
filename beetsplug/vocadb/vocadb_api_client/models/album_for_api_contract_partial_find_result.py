from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.album_for_api_contract import (
    AlbumForApiContract,
)


class AlbumForApiContractPartialFindResult(TaggedBase):
    total_count: int
    term: str | None = None
    items: list[AlbumForApiContract] | None = None
