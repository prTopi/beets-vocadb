"""Attrs classes related to API requests"""

from __future__ import annotations

import msgspec

from typing import Optional


class Artist(msgspec.Struct):
    additionalNames: str
    artistType: str
    deleted: bool
    id: int
    name: str
    status: str
    version: int
    pictureMime: Optional[str] = None


class AlbumArtist(msgspec.Struct, kw_only=True):
    categories: str
    effectiveRoles: str
    isSupport: bool
    name: str
    roles: str
    artist: Optional[Artist] = None


class SongArtist(AlbumArtist):
    id: int
    isCustomName: bool


class Tag(msgspec.Struct):
    name: str
    additionalNames: Optional[str] = None
    categoryName: Optional[str] = None
    id: Optional[int] = None
    urlSlug: Optional[str] = None


class TagUsage(msgspec.Struct):
    count: int
    tag: Tag


class AlbumOrSong(msgspec.Struct):
    """Base class with attributes shared by Album and Song"""

    artistString: str
    createDate: str
    defaultName: str
    defaultNameLanguage: str
    id: int
    name: str
    status: str


class Lyrics(msgspec.Struct):
    translationType: str
    value: str
    cultureCodes: list[str]
    id: Optional[int] = None
    source: Optional[str] = None
    url: Optional[str] = None


class Disc(msgspec.Struct):
    discNumber: int
    mediaType: str
    id: Optional[int] = None
    name: Optional[str] = None
    total: Optional[int] = None


class ReleaseDate(msgspec.Struct):
    isEmpty: bool
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None


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


class SongInAlbum(msgspec.Struct):
    discNumber: int
    trackNumber: int
    computedCultureCodes: list[str]
    id: Optional[int] = None
    name: Optional[str] = None
    song: Optional[Song] = None


class WebLink(msgspec.Struct):
    category: str
    description: str
    disabled: bool
    url: str
    descriptionOrUrl: Optional[str] = None
    id: Optional[int] = None


class AlbumFromQuery(AlbumOrSong):
    releaseDate: ReleaseDate
    discType: str


class Album(AlbumFromQuery):
    artists: list[AlbumArtist]
    tags: list[TagUsage]
    tracks: list[SongInAlbum]
    webLinks: list[WebLink]
    discs: list[Disc]
    catalogNumber: Optional[str] = None


class BaseQueryResult(msgspec.Struct):
    term: str
    totalCount: int


class SongQueryResult(BaseQueryResult):
    items: list[Song]


class AlbumQueryResult(BaseQueryResult):
    items: list[AlbumFromQuery]
