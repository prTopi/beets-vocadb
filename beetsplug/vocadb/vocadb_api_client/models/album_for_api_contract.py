from __future__ import annotations

from datetime import datetime

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.album_disc_properties_contract import (
    AlbumDiscPropertiesContract,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_for_album_for_api_contract import (
    ArtistForAlbumForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.content_language_selection import (
    ContentLanguageSelection,
)
from beetsplug.vocadb.vocadb_api_client.models.disc_type import DiscType
from beetsplug.vocadb.vocadb_api_client.models.entry_status import EntryStatus
from beetsplug.vocadb.vocadb_api_client.models.optional_date_time_contract import (
    OptionalDateTimeContract,
)
from beetsplug.vocadb.vocadb_api_client.models.song_in_album_for_api_contract import (
    SongInAlbumForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.tag_usage_for_api_contract import (
    TagUsageForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.web_link_for_api_contract import (
    WebLinkForApiContract,
)


class AlbumForApiContract(TaggedBase):
    create_date: datetime
    default_name_language: ContentLanguageSelection
    disc_type: DiscType
    id: int
    rating_average: float
    rating_count: int
    release_date: OptionalDateTimeContract
    status: EntryStatus
    version: int
    artists: list[ArtistForAlbumForApiContract] | None = None
    artist_string: str | None = None
    catalog_number: str | None = None
    default_name: str | None = None
    discs: list[AlbumDiscPropertiesContract] | None = None
    name: str | None = None
    tags: list[TagUsageForApiContract] | None = None
    tracks: list[SongInAlbumForApiContract] | None = None
    web_links: list[WebLinkForApiContract] | None = None
