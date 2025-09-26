__version__ = "0.0.1"

# Define package exports
__all__ = [
    "AlbumApiApi",
    "AlbumDiscPropertiesContract",
    "AlbumForApiContract",
    "AlbumForApiContractPartialFindResult",
    "AlbumOptionalFieldsSet",
    "AlbumOptionalFields",
    "AlbumSortRuleSet",
    "AlbumSortRule",
    "ApiClient",
    "ArtistCategories",
    "ArtistContract",
    "ArtistForAlbumForApiContract",
    "ArtistForSongContract",
    "ArtistRoles",
    "ArtistType",
    "ContentLanguagePreference",
    "ContentLanguageSelection",
    "DiscMediaType",
    "DiscType",
    "EntryStatus",
    "LyricsForSongContract",
    "NameMatchMode",
    "OptionalDateTimeContract",
    "PVServices",
    "SongApiApi",
    "SongForApiContract",
    "SongForApiContractPartialFindResult",
    "SongInAlbumForApiContract",
    "SongOptionalFieldsSet",
    "SongOptionalFields",
    "SongSortRule",
    "SongType",
    "TagBaseContract",
    "TagUsageForApiContract",
    "TranslationType",
    "WebLinkCategory",
    "WebLinkForApiContract",
]

# import apis into sdk package
from beetsplug.vocadb.vocadb_api_client.api import AlbumApiApi, SongApiApi
from beetsplug.vocadb.vocadb_api_client.api_client import ApiClient
from beetsplug.vocadb.vocadb_api_client.models.album_disc_properties_contract import (
    AlbumDiscPropertiesContract,
)
from beetsplug.vocadb.vocadb_api_client.models.album_for_api_contract import (
    AlbumForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.album_for_api_contract_partial_find_result import (
    AlbumForApiContractPartialFindResult,
)
from beetsplug.vocadb.vocadb_api_client.models.album_optional_fields import (
    AlbumOptionalFields,
    AlbumOptionalFieldsSet,
)
from beetsplug.vocadb.vocadb_api_client.models.album_sort_rule import (
    AlbumSortRule,
    AlbumSortRuleSet,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_categories import (
    ArtistCategories,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_contract import (
    ArtistContract,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_for_album_for_api_contract import (
    ArtistForAlbumForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_for_song_contract import (
    ArtistForSongContract,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_roles import ArtistRoles
from beetsplug.vocadb.vocadb_api_client.models.artist_type import ArtistType
from beetsplug.vocadb.vocadb_api_client.models.content_language_preference import (
    ContentLanguagePreference,
)
from beetsplug.vocadb.vocadb_api_client.models.content_language_selection import (
    ContentLanguageSelection,
)
from beetsplug.vocadb.vocadb_api_client.models.disc_media_type import (
    DiscMediaType,
)
from beetsplug.vocadb.vocadb_api_client.models.disc_type import DiscType
from beetsplug.vocadb.vocadb_api_client.models.entry_status import EntryStatus
from beetsplug.vocadb.vocadb_api_client.models.lyrics_for_song_contract import (
    LyricsForSongContract,
)
from beetsplug.vocadb.vocadb_api_client.models.name_match_mode import (
    NameMatchMode,
)
from beetsplug.vocadb.vocadb_api_client.models.optional_date_time_contract import (
    OptionalDateTimeContract,
)
from beetsplug.vocadb.vocadb_api_client.models.pv_services import PVServices
from beetsplug.vocadb.vocadb_api_client.models.song_for_api_contract import (
    SongForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.song_for_api_contract_partial_find_result import (
    SongForApiContractPartialFindResult,
)
from beetsplug.vocadb.vocadb_api_client.models.song_in_album_for_api_contract import (
    SongInAlbumForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.song_optional_fields import (
    SongOptionalFields,
    SongOptionalFieldsSet,
)
from beetsplug.vocadb.vocadb_api_client.models.song_sort_rule import (
    SongSortRule,
)
from beetsplug.vocadb.vocadb_api_client.models.song_type import SongType
from beetsplug.vocadb.vocadb_api_client.models.tag_base_contract import (
    TagBaseContract,
)
from beetsplug.vocadb.vocadb_api_client.models.tag_usage_for_api_contract import (
    TagUsageForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.translation_type import (
    TranslationType,
)
from beetsplug.vocadb.vocadb_api_client.models.web_link_category import (
    WebLinkCategory,
)
from beetsplug.vocadb.vocadb_api_client.models.web_link_for_api_contract import (
    WebLinkForApiContract,
)
