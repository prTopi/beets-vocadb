"""Attrs classes related to API requests"""
from __future__ import annotations

from attrs import define

from typing import TypeVar


@define
class Artist:
    additionalNames: str
    artistType: str
    deleted: bool
    id: int
    name: str
    status: str
    version: int
    pictureMime: str | None = None


@define(kw_only=True)
class AlbumArtist:
    categories: str
    effectiveRoles: str
    isSupport: bool
    name: str
    roles: str
    artist: Artist | None = None


@define
class SongArtist(AlbumArtist):
    id: int
    isCustomName: bool


@define
class Tag:
    name: str
    additionalNames: str | None = None
    categoryName: str | None = None
    id: int | None = None
    urlSlug: str | None = None


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
    id: int | None = None
    source: str | None = None
    url: str | None = None


@define
class Disc:
    discNumber: int
    mediaType: str
    id: int | None = None
    name: str | None = None
    total: int | None = None


@define
class ReleaseDate:
    isEmpty: bool
    day: int | None = None
    month: int | None = None
    year: int | None = None


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
    maxMilliBpm: int | None = None
    minMilliBpm: int | None = None
    publishDate: str | None = None


@define
class SongInAlbum:
    discNumber: int
    trackNumber: int
    computedCultureCodes: list[str]
    id: int | None = None
    name: str | None = None
    song: Song | None = None


@define
class WebLink:
    category: str
    description: str
    disabled: bool
    url: str
    descriptionOrUrl: str | None = None
    id: int | None = None


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
    catalogNumber: str | None = None


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
