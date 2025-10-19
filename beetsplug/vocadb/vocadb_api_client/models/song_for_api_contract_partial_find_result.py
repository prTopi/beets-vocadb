from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase
from beetsplug.vocadb.vocadb_api_client.models.song_for_api_contract import (
    SongForApiContract,
)


class SongForApiContractPartialFindResult(FrozenBase, frozen=True):
    total_count: int
    term: str | None = None
    items: tuple[SongForApiContract, ...] | None = None
