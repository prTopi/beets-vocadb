from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase
from beetsplug.vocadb.vocadb_api_client.models.album_for_api_contract import (
    AlbumForApiContract,
)


class AlbumForApiContractPartialFindResult(FrozenBase, frozen=True):
    total_count: int
    term: str | None = None
    items: tuple[AlbumForApiContract, ...] | None = None
