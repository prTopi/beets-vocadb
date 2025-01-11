from __future__ import annotations

import sys

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override
import weakref
from typing import TYPE_CHECKING, TypeVar, cast

import httpx
import msgspec

from .models import (
    Album,
    AlbumQueryResult,
    DiscType,
    Song,
    SongQueryResult,
    StrEnum,
)

if TYPE_CHECKING:
    from logging import Logger
    from typing import ClassVar

APIObjectT = TypeVar("APIObjectT", bound=msgspec.Struct)


class Language(StrEnum):
    ENGLISH = "English"
    JAPANESE = "Japanese"
    ROMAJI = "Romaji"

    DEFAULT = ENGLISH


class AlbumOptionalFields(StrEnum):
    NONE = "None"
    ADDITIONALNAMES = "AdditionalNames"
    ARTISTS = "Artists"
    DESCRIPTION = "Description"
    DISCS = "Discs"
    IDENTIFIERS = "Identifiers"
    MAINPICTURE = "MainPicture"
    NAMES = "Names"
    PVS = "PVs"
    RELEASEEVENT = "ReleaseEvent"
    TAGS = "Tags"
    TRACKS = "Tracks"
    WEBLINKS = "WebLinks"


class AlbumSortRule(StrEnum):
    NONE = "None"
    NAME = "Name"
    RELEASEDATE = "ReleaseDate"
    RELEASEDATEWITHNULLS = "ReleaseDateWithNulls"
    ADDITIONDATE = "AdditionDate"
    RATINGAVERAGE = "RatingAverage"
    RATINGTOTAL = "RatingTotal"
    NAMETHENRELEASEDATE = "NameThenReleaseDate"
    COLLECTIONCOUNT = "CollectionCount"


class SongOptionalFields(StrEnum):
    NONE = "None"
    ADDIATIONALNAMES = "AdditionalNames"
    ALBUMS = "Albums"
    ARTISTS = "Artists"
    LYRICS = "Lyrics"
    MAINPICTURE = "MainPicture"
    NAMES = "Names"
    PVS = "PVs"
    RELEASEEVENT = "ReleaseEvent"
    TAGS = "Tags"
    THUMBURL = "ThumbUrl"
    WEBLINKS = "WebLinks"
    BPM = "Bpm"
    CULTURECODES = "CultureCodes"


class SongSortRule(StrEnum):
    NONE = "None"
    NAME = "Name"
    ADDITIONDATE = "AdditionDate"
    PUBLISHDATE = "PublishDate"
    FAVORITEDTIMES = "FavoritedTimes"
    RATINGSCORE = "RatingScore"
    TAGUSAGECOUNT = "TagUsageCount"
    SONGTYPE = "SongType"


class NameMatchMode(StrEnum):
    AUTO = "Auto"
    PARTIAL = "Partial"
    STARTSWITH = "StartsWith"
    EXACT = "Exact"
    WORDS = "Words"


class ParamsBase(
    msgspec.Struct,
    forbid_unknown_fields=True,
    omit_defaults=True,
    rename="camel",
):
    @property
    def asdict(self) -> dict[str, str]:
        """Convert the ParamsBase instance to a dictionary suitable for httpx."""
        raise NotImplementedError


class GetParamsBase(ParamsBase, kw_only=True):
    lang: Language


class GetAlbumParams(GetParamsBase):
    fields: set[AlbumOptionalFields]
    song_fields: set[SongOptionalFields]

    @property
    @override
    def asdict(self) -> dict[str, str]:
        return {
            "lang": self.lang.value,
            "fields": ",".join(field.value for field in self.fields),
            "songFields": ",".join(
                song_field.value for song_field in self.song_fields
            ),
        }


class GetSongParams(GetParamsBase):
    fields: set[SongOptionalFields]

    @property
    @override
    def asdict(self) -> dict[str, str]:
        return {
            "lang": self.lang.value,
            "fields": ",".join(field.value for field in self.fields),
        }


class SearchParamsBase(ParamsBase):
    query: str
    max_results: int
    name_match_mode: NameMatchMode


class SearchAlbumsParams(SearchParamsBase):
    @property
    @override
    def asdict(self) -> dict[str, str]:
        return {
            "query": self.query,
            "maxResults": str(self.max_results),
            "nameMatchMode": self.name_match_mode.value,
        }


class SearchSongParams(SearchParamsBase):
    disc_types: DiscType
    fields: set[SongOptionalFields]
    prefer_accurate_matches: bool
    sort: SongSortRule
    lang: Language

    @property
    @override
    def asdict(self) -> dict[str, str]:
        return {
            "query": self.query,
            "maxResults": str(self.max_results),
            "nameMatchMode": self.name_match_mode.value,
            "discTypes": self.disc_types.value,
            "fields": ",".join(field.value for field in self.fields),
            "preferAccurateMatches": str(self.prefer_accurate_matches),
            "sort": self.sort.value,
            "lang": self.lang.value,
        }


class RequestsHandler:
    """
    An interface to the VocaDB API.
    Can be subclassed to use a different instance.
    """

    base_url: str = "https://vocadb.net/api/"

    _decoders: ClassVar[
        dict[type[msgspec.Struct], msgspec.json.Decoder[msgspec.Struct]]
    ] = {}

    def __init__(
        self,
        user_agent: str,
        logger: Logger,
        timeout: float = 10,
    ) -> None:
        self._log: Logger = logger
        self._client: httpx.Client = httpx.Client(
            base_url=httpx.URL(self.base_url),
            headers={"accept": "application/json", "User-Agent": user_agent},
            http2=True,
            timeout=timeout,
        )
        _ = weakref.finalize(self, self.close)

    def __init_subclass__(cls, base_url: str) -> None:
        cls.base_url = base_url

    @classmethod
    def _get_decoder(
        cls, type: type[APIObjectT]
    ) -> msgspec.json.Decoder[APIObjectT]:
        """Caches and returns a decoder for the specified type"""
        decoder: msgspec.json.Decoder[APIObjectT] = msgspec.json.Decoder(
            type=type
        )
        cls._decoders[type] = cast(
            msgspec.json.Decoder[msgspec.Struct], decoder
        )
        return decoder

    def _get(
        self, relative_path: str, params: ParamsBase, type: type[APIObjectT]
    ) -> APIObjectT | None:
        """Makes a GET request to the API and returns structured response data.

        Args:
            path: API endpoint path to request
            params: instance of (a subclass of) ParamsBase

        Returns:
            Structured response data if successful, None if request fails
        """
        params_dict: dict[str, str] = params.asdict
        try:
            response: httpx.Response = self._client.get(
                relative_path, params=params_dict
            )
            _ = response.raise_for_status()
        except httpx.HTTPError as e:
            self._log.error("Error fetching data - {}", e)
            return None

        decoder: msgspec.json.Decoder[APIObjectT]
        try:
            decoder = cast(
                msgspec.json.Decoder[APIObjectT], self._decoders[type]
            )
        except KeyError:
            self._log.debug("Getting decoder for {}", type)
            decoder = self._get_decoder(type)
        return decoder.decode(response.content)

    def get_album(
        self,
        album_id: int,
        params: GetAlbumParams,
    ) -> Album | None:
        """Fetches an album by its ID."""
        return self._get(
            relative_path=f"albums/{album_id}",
            params=params,
            type=Album,
        )

    def get_song(
        self,
        song_id: int,
        params: GetSongParams,
    ) -> Song | None:
        """Fetches a song by its ID."""
        return self._get(
            relative_path=f"songs/{song_id}",
            params=params,
            type=Song,
        )

    def search_albums(
        self, params: SearchAlbumsParams
    ) -> AlbumQueryResult | None:
        """Searches for albums by a query string."""
        return self._get(
            relative_path="albums",
            params=params,
            type=AlbumQueryResult,
        )

    def search_songs(self, params: SearchSongParams) -> SongQueryResult | None:
        """Searches for songs by a query string."""
        return self._get(
            relative_path="songs",
            params=params,
            type=SongQueryResult,
        )

    # TODO: better error handling, more parameters

    def close(self) -> None:
        self._log.debug("Closing {}", self._client)
        self._client.close()
