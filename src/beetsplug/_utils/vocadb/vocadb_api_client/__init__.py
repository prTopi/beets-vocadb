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
    "ArtistRolesSet",
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
from .api import AlbumApiApi, SongApiApi
from .api_client import ApiClient
from .models.album_disc_properties_contract import AlbumDiscPropertiesContract
from .models.album_for_api_contract import AlbumForApiContract
from .models.album_for_api_contract_partial_find_result import (
    AlbumForApiContractPartialFindResult,
)
from .models.album_optional_fields import (
    AlbumOptionalFields,
    AlbumOptionalFieldsSet,
)
from .models.album_sort_rule import AlbumSortRule, AlbumSortRuleSet
from .models.artist_categories import ArtistCategories
from .models.artist_contract import ArtistContract
from .models.artist_for_album_for_api_contract import (
    ArtistForAlbumForApiContract,
)
from .models.artist_for_song_contract import ArtistForSongContract
from .models.artist_roles import ArtistRoles, ArtistRolesSet
from .models.artist_type import ArtistType
from .models.content_language_preference import ContentLanguagePreference
from .models.content_language_selection import ContentLanguageSelection
from .models.disc_media_type import DiscMediaType
from .models.disc_type import DiscType
from .models.entry_status import EntryStatus
from .models.lyrics_for_song_contract import LyricsForSongContract
from .models.name_match_mode import NameMatchMode
from .models.optional_date_time_contract import OptionalDateTimeContract
from .models.pv_services import PVServices
from .models.song_for_api_contract import SongForApiContract
from .models.song_for_api_contract_partial_find_result import (
    SongForApiContractPartialFindResult,
)
from .models.song_in_album_for_api_contract import SongInAlbumForApiContract
from .models.song_optional_fields import (
    SongOptionalFields,
    SongOptionalFieldsSet,
)
from .models.song_sort_rule import SongSortRule
from .models.song_type import SongType
from .models.tag_base_contract import TagBaseContract
from .models.tag_usage_for_api_contract import TagUsageForApiContract
from .models.translation_type import TranslationType
from .models.web_link_category import WebLinkCategory
from .models.web_link_for_api_contract import WebLinkForApiContract
