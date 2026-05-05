__version__ = "0.0.1"

# Define package exports
__all__ = [
    "AlbumApiApi",
    "AlbumDiscPropertiesContract",
    "AlbumForApiContract",
    "AlbumForApiContractPartialFindResult",
    "AlbumOptionalFieldsSet",
    "AlbumOptionalFields",
    "AlbumSortRule",
    "ApiClient",
    "ArtistApiApi",
    "ArtistCategories",
    "ArtistContract",
    "ArtistForAlbumForApiContract",
    "ArtistForApiContract",
    "ArtistForArtistForApiContract",
    "ArtistLinkType",
    "ArtistForSongContract",
    "ArtistOptionalFields",
    "ArtistOptionalFieldsSet",
    "ArtistRelationsFields",
    "ArtistRelationsFieldsSet",
    "ArtistParticipationStatus",
    "ArtistRoles",
    "ArtistRolesSet",
    "ArtistType",
    "ContentLanguagePreference",
    "ContentLanguageSelection",
    "DiscMediaType",
    "DiscType",
    "EnglishTranslatedStringContract",
    "EntryStatus",
    "LocalizedStringContract",
    "LocalizedStringWithIdContract",
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
    "TagApiApi",
    "TagBaseContract",
    "TagForApiContract",
    "TagForApiContractPartialFindResult",
    "TagOptionalFields",
    "TagOptionalFieldsSet",
    "TagSortRule",
    "TagUsageForApiContract",
    "TranslationType",
    "WebLinkCategory",
    "WebLinkForApiContract",
]

# import apis into sdk package
from .api import AlbumApiApi, ArtistApiApi, SongApiApi, TagApiApi
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
from .models.album_sort_rule import AlbumSortRule
from .models.artist_categories import ArtistCategories
from .models.artist_contract import ArtistContract
from .models.artist_for_album_for_api_contract import (
    ArtistForAlbumForApiContract,
)
from .models.artist_for_api_contract import ArtistForApiContract
from .models.artist_for_artist_for_api_contract import (
    ArtistForArtistForApiContract,
)
from .models.artist_for_song_contract import ArtistForSongContract
from .models.artist_link_type import ArtistLinkType
from .models.artist_optional_fields import (
    ArtistOptionalFields,
    ArtistOptionalFieldsSet,
)
from .models.artist_participation_status import ArtistParticipationStatus
from .models.artist_relations_fields import (
    ArtistRelationsFields,
    ArtistRelationsFieldsSet,
)
from .models.artist_roles import ArtistRoles, ArtistRolesSet
from .models.artist_type import ArtistType
from .models.content_language_preference import ContentLanguagePreference
from .models.content_language_selection import ContentLanguageSelection
from .models.disc_media_type import DiscMediaType
from .models.disc_type import DiscType
from .models.english_translated_string_contract import (
    EnglishTranslatedStringContract,
)
from .models.entry_status import EntryStatus
from .models.localized_string_contract import LocalizedStringContract
from .models.localized_string_with_id_contract import (
    LocalizedStringWithIdContract,
)
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
from .models.tag_for_api_contract import TagForApiContract
from .models.tag_for_api_contract_partial_find_result import (
    TagForApiContractPartialFindResult,
)
from .models.tag_optional_fields import TagOptionalFields, TagOptionalFieldsSet
from .models.tag_sort_rule import TagSortRule
from .models.tag_usage_for_api_contract import TagUsageForApiContract
from .models.translation_type import TranslationType
from .models.web_link_category import WebLinkCategory
from .models.web_link_for_api_contract import WebLinkForApiContract
