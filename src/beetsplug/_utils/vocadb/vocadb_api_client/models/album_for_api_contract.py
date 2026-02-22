from __future__ import annotations

from datetime import datetime

from . import FrozenBase
from .album_disc_properties_contract import AlbumDiscPropertiesContract
from .artist_for_album_for_api_contract import ArtistForAlbumForApiContract
from .content_language_selection import ContentLanguageSelection
from .disc_type import DiscType
from .entry_status import EntryStatus
from .entry_thumb_for_api_contract import EntryThumbForApiContract
from .optional_date_time_contract import OptionalDateTimeContract
from .song_in_album_for_api_contract import SongInAlbumForApiContract
from .tag_usage_for_api_contract import TagUsageForApiContract
from .web_link_for_api_contract import WebLinkForApiContract


class AlbumForApiContract(FrozenBase, frozen=True):
    create_date: datetime
    default_name_language: ContentLanguageSelection
    disc_type: DiscType
    id: int
    rating_average: float
    rating_count: int
    release_date: OptionalDateTimeContract
    status: EntryStatus
    version: int
    artists: tuple[ArtistForAlbumForApiContract, ...] | None = None
    artist_string: str | None = None
    catalog_number: str | None = None
    default_name: str | None = None
    discs: tuple[AlbumDiscPropertiesContract, ...] | None = None
    main_picture: EntryThumbForApiContract | None = None
    name: str | None = None
    tags: tuple[TagUsageForApiContract, ...] | None = None
    tracks: tuple[SongInAlbumForApiContract, ...] | None = None
    web_links: tuple[WebLinkForApiContract, ...] | None = None
