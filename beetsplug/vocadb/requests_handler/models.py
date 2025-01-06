"""Attrs classes related to API requests"""

from typing import Optional, TypeVar

from attrs import define


@define
class Artist:
    additionalNames: str
    artistType: str
    deleted: bool
    id: int
    name: str
    status: str
    version: int
    pictureMime: Optional[str] = None


@define(kw_only=True)
class AlbumArtist:
    categories: str
    effectiveRoles: str
    isSupport: bool
    name: str
    roles: str
    artist: Optional[Artist] = None


@define
class SongArtist(AlbumArtist):
    id: int
    isCustomName: bool


@define
class Tag:
    name: str
    additionalNames: Optional[str] = None
    categoryName: Optional[str] = None
    id: Optional[int] = None
    urlSlug: Optional[str] = None


@define
class TagUsage:
    count: int
    tag: Tag


@define
class AlbumOrSong:
    """Base class with attributes shared by Album and Song"""

    artistString: str
    createDate: str
    defaultName: str
    defaultNameLanguage: str
    id: int
    name: str
    status: str


@define
class Lyrics:
    translationType: str
    value: str
    cultureCodes: list[str]
    id: Optional[int] = None
    source: Optional[str] = None
    url: Optional[str] = None


@define
class Disc:
    discNumber: int
    mediaType: str
    id: Optional[int] = None
    name: Optional[str] = None
    total: Optional[int] = None


@define
class ReleaseDate:
    isEmpty: bool
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None


@define
class Song(AlbumOrSong):
    artists: list[SongArtist]
    cultureCodes: list[str]
    favoritedTimes: int
    lengthSeconds: float
    lyrics: list[Lyrics]
    pvServices: str
    ratingScore: int
    songType: str
    tags: list[TagUsage]
    version: int
    maxMilliBpm: Optional[int] = None
    minMilliBpm: Optional[int] = None
    publishDate: Optional[str] = None


@define
class SongInAlbum:
    discNumber: int
    trackNumber: int
    computedCultureCodes: list[str]
    id: Optional[int] = None
    name: Optional[str] = None
    song: Optional[Song] = None


@define
class WebLink:
    category: str
    description: str
    disabled: bool
    url: str
    descriptionOrUrl: Optional[str] = None
    id: Optional[int] = None


@define
class AlbumFromQuery(AlbumOrSong):
    releaseDate: ReleaseDate
    discType: str


@define
class Album(AlbumFromQuery):
    artists: list[AlbumArtist]
    tags: list[TagUsage]
    tracks: list[SongInAlbum]
    webLinks: list[WebLink]
    discs: list[Disc]
    catalogNumber: Optional[str] = None


@define
class BaseQueryResult:
    term: str
    totalCount: int


@define
class SongQueryResult(BaseQueryResult):
    items: list[Song]


@define
class AlbumQueryResult(BaseQueryResult):
    items: list[AlbumFromQuery]


APIObjectT = TypeVar("APIObjectT", Album, AlbumQueryResult, Song, SongQueryResult)
