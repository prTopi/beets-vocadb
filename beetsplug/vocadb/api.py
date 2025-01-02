"""Things related to API requests"""

from sys import version_info
from typing import NamedTuple, Optional, Sequence, TypedDict

if version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

import beets

USER_AGENT: str = f"beets/{beets.__version__} +https://beets.io/"
HEADERS: dict[str, str] = {"accept": "application/json", "User-Agent": USER_AGENT}


class InstanceInfo(NamedTuple):
    """Information about a specific instance of VocaDB"""

    name: str
    base_url: str
    api_url: str
    subcommand: str


class ArtistDict(TypedDict):
    additionalNames: str
    artistType: str
    deleted: bool
    id: int
    name: str
    pictureMime: str
    status: str
    version: int


class AlbumOrSongArtistDict(TypedDict):
    artist: Optional[ArtistDict]
    categories: str
    effectiveRoles: str
    id: NotRequired[int]
    isCustomName: NotRequired[bool]
    isSupport: bool
    name: str
    roles: str


class TagDict(TypedDict):
    additionalNames: NotRequired[str]
    categoryName: NotRequired[str]
    id: NotRequired[int]
    name: str
    urlSlug: NotRequired[str]


class TagUsageDict(TypedDict):
    count: int
    tag: TagDict


class InfoDict(TypedDict):
    artistString: str
    createDate: str
    defaultName: str
    defaultNameLanguage: str
    id: int
    name: str
    status: str
    tags: list[TagUsageDict]


class LyricsDict(TypedDict):
    cultureCodes: list[str]
    id: NotRequired[int]
    source: NotRequired[str]
    translationType: str
    url: NotRequired[str]
    value: str


class DiscDict(TypedDict):
    discNumber: int
    id: NotRequired[int]
    mediaType: str
    name: NotRequired[str]
    total: NotRequired[int]


class ReleaseDateDict(TypedDict):
    day: NotRequired[int]
    isEmpty: bool
    month: NotRequired[int]
    year: NotRequired[int]


class SongDict(InfoDict):
    artists: list[AlbumOrSongArtistDict]
    favoritedTimes: int
    lengthSeconds: int
    lyrics: list[LyricsDict]
    maxMilliBpm: int
    minMilliBpm: int
    publishDate: str
    pvServices: str
    ratingScore: int
    songType: str
    version: int
    cultureCodes: list[str]


class SongInAlbumDict(TypedDict):
    discNumber: int
    id: NotRequired[int]
    name: NotRequired[str]
    song: SongDict
    trackNumber: int
    computedCultureCodes: list[str]


class WebLinkDict(TypedDict):
    category: str
    description: str
    descriptionOrUrl: str
    disabled: bool
    id: NotRequired[int]
    url: str


class AlbumDict(InfoDict):
    artists: list[AlbumOrSongArtistDict]
    catalogNumber: NotRequired[str]
    discs: Sequence[DiscDict]
    discType: NotRequired[str]
    releaseDate: ReleaseDateDict
    tracks: list[SongInAlbumDict]
    webLinks: list[WebLinkDict]


class FindResultDict(TypedDict):
    id: NotRequired[int]
    term: str
    totalCount: int


class SongFindResultDict(FindResultDict):
    items: list[SongDict]


class AlbumFindResultDict(FindResultDict):
    items: list[AlbumDict]
