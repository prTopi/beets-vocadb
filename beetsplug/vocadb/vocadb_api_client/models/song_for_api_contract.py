from __future__ import annotations

import sys
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

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


class SongForApiContract(TaggedBase, dict=True):
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
    artists: tuple[ArtistForSongContract, ...] | None = None
    artist_string: str | None = None
    culture_codes: set[str] | None = None
    default_name: str | None = None
    lyrics: tuple[LyricsForSongContract, ...] | None = None
    name: str | None = None
    original_version_id: int | None = None
    tags: tuple[TagUsageForApiContract, ...] | None = None
    max_milli_bpm: int | None = None
    min_milli_bpm: int | None = None
    publish_date: datetime | None = None

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self.create_date,
                self.default_name_language,
                self.id,
                self.rating_score,
                self.version,
                self.favorited_times,
                self.length_seconds,
                self._pv_services,
                self.song_type,
                self.status,
                self.artists,
                self.artist_string,
                self.culture_codes,
                self.default_name,
                self.lyrics,
                self.name,
                self.original_version_id,
                self.tags,
                self.max_milli_bpm,
                self.min_milli_bpm,
                self.publish_date,
            )
        )

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SongForApiContract):
            return False
        return (
            self.create_date == other.create_date
            and self.default_name_language == other.default_name_language
            and self.id == other.id
            and self.rating_score == other.rating_score
            and self.version == other.version
            and self.favorited_times == other.favorited_times
            and self.length_seconds == other.length_seconds
            and self._pv_services == other._pv_services
            and self.song_type == other.song_type
            and self.status == other.status
            and self.artists == other.artists
            and self.artist_string == other.artist_string
            and self.culture_codes == other.culture_codes
            and self.default_name == other.default_name
            and self.lyrics == other.lyrics
            and self.name == other.name
            and self.original_version_id == other.original_version_id
            and self.tags == other.tags
            and self.max_milli_bpm == other.max_milli_bpm
            and self.min_milli_bpm == other.min_milli_bpm
            and self.publish_date == other.publish_date
        )

    @cached_property
    def pv_services(self) -> StrEnumSet[PVServices]:
        return StrEnumSet[PVServices].from_delimited_str(
            PVServices, self._pv_services
        )
