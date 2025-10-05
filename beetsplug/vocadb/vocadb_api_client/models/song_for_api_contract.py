from __future__ import annotations

from datetime import datetime
from functools import cached_property

import msgspec

from beetsplug.vocadb.vocadb_api_client.models import StrEnumSet, TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.artist_for_song_contract import (
    ArtistForSongContract,
)
from beetsplug.vocadb.vocadb_api_client.models.content_language_selection import (
    ContentLanguageSelection,
)
from beetsplug.vocadb.vocadb_api_client.models.entry_status import EntryStatus
from beetsplug.vocadb.vocadb_api_client.models.lyrics_for_song_contract import (
    LyricsForSongContract,
)
from beetsplug.vocadb.vocadb_api_client.models.pv_services import PVServices
from beetsplug.vocadb.vocadb_api_client.models.song_type import SongType
from beetsplug.vocadb.vocadb_api_client.models.tag_usage_for_api_contract import (
    TagUsageForApiContract,
)


class SongForApiContract(TaggedBase):
    create_date: datetime
    default_name_language: ContentLanguageSelection
    id: int
    rating_score: int
    version: int
    favorited_times: int
    length_seconds: int
    _pv_services: str = msgspec.field(name="pvServices")
    song_type: SongType
    status: EntryStatus
    artists: list[ArtistForSongContract] | None = None
    artist_string: str | None = None
    culture_codes: set[str] | None = None
    default_name: str | None = None
    lyrics: list[LyricsForSongContract] | None = None
    name: str | None = None
    original_version_id: int | None = None
    tags: list[TagUsageForApiContract] | None = None
    max_milli_bpm: int | None = None
    min_milli_bpm: int | None = None
    publish_date: datetime | None = None

    @cached_property
    def pv_services(self) -> StrEnumSet[PVServices]:
        return StrEnumSet[PVServices].from_csv(PVServices, self._pv_services)
