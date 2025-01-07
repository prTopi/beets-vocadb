"""Attrs classes related to API requests"""

from __future__ import annotations

import msgspec

from typing import Optional

class TaggedBase(msgspec.Struct, rename="camel"): ...

class Artist(TaggedBase):
    additional_names: str
    artist_type: str
    deleted: bool
    id: int
    name: str
    status: str
    version: int
    picture_mime: Optional[str] = None


class AlbumArtist(TaggedBase, kw_only=True):
    categories: str
    effective_roles: str
    is_support: bool
    name: str
    roles: str
    artist: Optional[Artist] = None


class SongArtist(AlbumArtist):
    id: int
    is_custom_name: bool


class Tag(TaggedBase):
    name: str
    additional_names: Optional[str] = None
    category_name: Optional[str] = None
    id: Optional[int] = None
    url_slug: Optional[str] = None


class TagUsage(TaggedBase):
    count: int
    tag: Tag


class AlbumOrSong(TaggedBase):
    """Base class with attributes shared by Album and Song"""

    artist_string: str
    create_date: str
    default_name: str
    default_name_language: str
    id: int
    name: str
    status: str


class Lyrics(TaggedBase):
    translation_type: str
    value: str
    culture_codes: list[str]
    id: Optional[int] = None
    source: Optional[str] = None
    url: Optional[str] = None


class Disc(TaggedBase):
    disc_number: int
    media_type: str
    id: Optional[int] = None
    name: Optional[str] = None
    total: Optional[int] = None


class ReleaseDate(TaggedBase):
    is_empty: bool
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None


class Song(AlbumOrSong):
    artists: list[SongArtist]
    culture_codes: list[str]
    favorited_times: int
    length_seconds: float
    lyrics: list[Lyrics]
    pv_services: str
    rating_score: int
    song_type: str
    tags: list[TagUsage]
    version: int
    max_milli_bpm: Optional[int] = None
    min_milli_bpm: Optional[int] = None
    publish_date: Optional[str] = None


class SongInAlbum(TaggedBase):
    disc_number: int
    track_number: int
    computed_culture_codes: list[str]
    id: Optional[int] = None
    name: Optional[str] = None
    song: Optional[Song] = None


class WebLink(TaggedBase):
    category: str
    description: str
    disabled: bool
    url: str
    description_or_url: Optional[str] = None
    id: Optional[int] = None


class AlbumFromQuery(AlbumOrSong):
    release_date: ReleaseDate
    disc_type: str


class Album(AlbumFromQuery):
    artists: list[AlbumArtist]
    tags: list[TagUsage]
    tracks: list[SongInAlbum]
    web_links: list[WebLink]
    discs: list[Disc]
    catalog_number: Optional[str] = None


class BaseQueryResult(TaggedBase):
    term: str
    total_count: int


class SongQueryResult(BaseQueryResult):
    items: list[Song]


class AlbumQueryResult(BaseQueryResult):
    items: list[AlbumFromQuery]
