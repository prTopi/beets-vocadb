from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.song_for_api_contract import (
    SongForApiContract,
)


class SongInAlbumForApiContract(TaggedBase):
    disc_number: int
    id: int
    track_number: int
    song: SongForApiContract | None = None
    computed_culture_codes: set[str] | None = None
    name: str | None = None
