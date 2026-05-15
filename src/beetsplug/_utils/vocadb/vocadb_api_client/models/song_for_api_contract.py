from __future__ import annotations

from .album_contract import AlbumContract
from .artist_for_song_contract import ArtistForSongContract
from .content_language_selection import ContentLanguageSelection
from .entry_thumb_for_api_contract import EntryThumbForApiContract
from .localized_string_contract import LocalizedStringContract
from .lyrics_for_song_contract import LyricsForSongContract
from .song_contract import SongContract
from .tag_usage_for_api_contract import TagUsageForApiContract
from .web_link_for_api_contract import WebLinkForApiContract


class SongForApiContract(SongContract, frozen=True, dict=True, kw_only=True):
    albums: tuple[AlbumContract, ...] | None = None
    artists: tuple[ArtistForSongContract, ...] | None = None
    culture_codes: tuple[str, ...] | None = None
    default_name: str | None = None
    default_name_language: ContentLanguageSelection
    lyrics: tuple[LyricsForSongContract, ...] | None = None
    main_picture: EntryThumbForApiContract | None = None
    max_milli_bpm: int | None = None
    merged_to: int | None = None
    min_milli_bpm: int | None = None
    names: tuple[LocalizedStringContract, ...] | None = None
    original_version_id: int | None = None
    # pvs: tuple[PVContract] | None = None
    # release_event: ReleaseEventForApiContract | None = None
    # release_events: tuple[ReleaseEventForApiContract, ...] | None = None
    tags: tuple[TagUsageForApiContract, ...] | None = None
    web_links: tuple[WebLinkForApiContract, ...] | None = None
