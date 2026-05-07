from __future__ import annotations

from .album_contract import AlbumContract
from .album_disc_properties_contract import AlbumDiscPropertiesContract
from .artist_for_album_for_api_contract import ArtistForAlbumForApiContract
from .content_language_selection import ContentLanguageSelection
from .entry_thumb_for_api_contract import EntryThumbForApiContract
from .localized_string_contract import LocalizedStringContract
from .song_in_album_for_api_contract import SongInAlbumForApiContract
from .tag_usage_for_api_contract import TagUsageForApiContract
from .web_link_for_api_contract import WebLinkForApiContract


class AlbumForApiContract(AlbumContract, frozen=True, kw_only=True):
    artists: tuple[ArtistForAlbumForApiContract, ...] | None = None
    barcode: str | None = None
    catalog_number: str | None = None
    cover_picture_mime: None = None  # only AlbumContract has this field
    default_name: str | None = None
    default_name_language: ContentLanguageSelection
    description: str | None = None
    discs: tuple[AlbumDiscPropertiesContract, ...] | None = None
    # identifiers: tuple[AlbumIdentifierContract, ...] | None = None
    main_picture: EntryThumbForApiContract | None = None
    merged_to: int | None = None
    names: tuple[LocalizedStringContract, ...] | None = None
    # pvs: tuple[PVContract] | None = None
    # release_events: tuple[ReleaseEventForApiContract, ...] | None = None
    tags: tuple[TagUsageForApiContract, ...] | None = None
    tracks: tuple[SongInAlbumForApiContract, ...] | None = None
    web_links: tuple[WebLinkForApiContract, ...] | None = None
