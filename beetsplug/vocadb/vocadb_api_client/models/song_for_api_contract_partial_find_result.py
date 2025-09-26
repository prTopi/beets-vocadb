from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.song_for_api_contract import (
    SongForApiContract,
)


class SongForApiContractPartialFindResult(TaggedBase):
    total_count: int
    term: str | None = None
    items: list[SongForApiContract] | None = None
