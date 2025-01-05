"""Things related to API requests"""

from dataclasses import dataclass
from typing import Optional

import beets

USER_AGENT: str = f"beets/{beets.__version__} +https://beets.io/"
HEADERS: dict[str, str] = {"accept": "application/json", "User-Agent": USER_AGENT}
SONG_FIELDS = "Artists,CultureCodes,Tags,Bpm,Lyrics"


@dataclass(frozen=True)
class InstanceInfo:
    """Information about a specific instance of VocaDB"""

    name: str
    base_url: str
    api_url: str
    subcommand: str


@dataclass(frozen=True)
class ArtistInResponse:

    additionalNames: str
    artistType: str
    deleted: bool
    id: int
    name: str
    status: str
    version: int
    pictureMime: Optional[str] = None


@dataclass
class AlbumOrSongArtistInResponse:

    categories: str
    effectiveRoles: str
    isSupport: bool
    name: str
    roles: str
    artist: Optional[ArtistInResponse] = None
    id: Optional[int] = None
    isCustomName: Optional[bool] = None


@dataclass(frozen=True)
class TagFromAPI:

    name: str
    additionalNames: Optional[str] = None
    categoryName: Optional[str] = None
    id: Optional[int] = None
    urlSlug: Optional[str] = None


@dataclass(frozen=True)
class TagUsageInResponse:

    count: int
    tag: TagFromAPI


@dataclass(frozen=True)
class BaseInfoFromAPI:

    artistString: str
    createDate: str
    defaultName: str
    defaultNameLanguage: str
    id: int
    name: str
    status: str


@dataclass(frozen=True)
class LyricsFromAPI:

    translationType: str
    value: str
    cultureCodes: list[str]
    id: Optional[int] = None
    source: Optional[str] = None
    url: Optional[str] = None


@dataclass
class DiscInResponse:

    discNumber: int
    mediaType: str
    id: Optional[int] = None
    name: Optional[str] = None
    total: Optional[int] = None


@dataclass(frozen=True)
class ReleaseDateInResponse:

    isEmpty: bool
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None


@dataclass(frozen=True)
class SongFromAPI(BaseInfoFromAPI):

    artists: list[AlbumOrSongArtistInResponse]
    cultureCodes: list[str]
    favoritedTimes: int
    lengthSeconds: float
    lyrics: list[LyricsFromAPI]
    pvServices: str
    ratingScore: int
    songType: str
    tags: list[TagUsageInResponse]
    version: int
    maxMilliBpm: Optional[int] = None
    minMilliBpm: Optional[int] = None
    publishDate: Optional[str] = None


@dataclass(frozen=True)
class SongInAlbumInResponse:

    discNumber: int
    trackNumber: int
    computedCultureCodes: list[str]
    id: Optional[int] = None
    name: Optional[str] = None
    song: Optional[SongFromAPI] = None


@dataclass(frozen=True)
class WebLinkInResponse:

    category: str
    description: str
    disabled: bool
    url: str
    descriptionOrUrl: Optional[str] = None
    id: Optional[int] = None


@dataclass(frozen=True)
class AlbumCandidate(BaseInfoFromAPI):

    releaseDate: ReleaseDateInResponse
    discType: str


@dataclass(frozen=True)
class AlbumFromAPI(AlbumCandidate):

    artists: list[AlbumOrSongArtistInResponse]
    tags: list[TagUsageInResponse]
    tracks: list[SongInAlbumInResponse]
    webLinks: list[WebLinkInResponse]
    discs: list[DiscInResponse]
    catalogNumber: Optional[str] = None


@dataclass(frozen=True)
class BaseFindResultFromAPI:

    term: str
    totalCount: int


@dataclass(frozen=True)
class ItemCandidatesFromAPI(BaseFindResultFromAPI):

    items: list[SongFromAPI]


@dataclass(frozen=True)
class CandidatesFromAPI(BaseFindResultFromAPI):

    items: list[AlbumCandidate]
