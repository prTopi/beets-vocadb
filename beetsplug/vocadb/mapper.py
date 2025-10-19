from __future__ import annotations

from enum import auto
from typing import TYPE_CHECKING

import httpx
from beets.autotag.hooks import AlbumInfo, TrackInfo

from beetsplug.vocadb.artists import get_album_artists, get_track_artists
from beetsplug.vocadb.lyrics_processor import LyricsProcessor
from beetsplug.vocadb.plugin_config import VA_NAME
from beetsplug.vocadb.utils import (
    discs_fallback,
    get_asin,
    get_bpm,
    get_genres,
    group_tracks_by_disc,
)
from beetsplug.vocadb.vocadb_api_client import (
    ContentLanguagePreference,
    DiscMediaType,
    DiscType,
    OptionalDateTimeContract,
)
from beetsplug.vocadb.vocadb_api_client.models import StrEnum

if TYPE_CHECKING:
    from datetime import datetime

    from beetsplug.vocadb.vocadb_api_client import (
        AlbumDiscPropertiesContract,
        AlbumForApiContract,
        OptionalDateTimeContract,
        SongForApiContract,
        SongInAlbumForApiContract,
    )


class AlbumFlexibleAttributes(StrEnum):
    ALBUM_ID = auto()
    ALBUMARTIST_ID = auto()
    ALBUMARTIST_IDS = auto()


class ItemFlexibleAttributes(StrEnum):
    TRACK_ID = auto()
    ARTIST_ID = auto()
    ARTIST_IDS = auto()


# TODO: this sucks
class FlexibleAttributes:
    def __init__(self, prefix: str) -> None:
        """Add prefix to all attributes in each field.

        Args:
            prefix: String prefix to add to attribute names

        Returns:
            New FlexibleAttributes instance with prefixed attributes
        """

        self.album: dict[AlbumFlexibleAttributes, str] = {
            arg: f"{prefix}_{arg}" for arg in AlbumFlexibleAttributes
        }
        self.item: dict[ItemFlexibleAttributes, str] = {
            arg: f"{prefix}_{arg}" for arg in ItemFlexibleAttributes
        }


class Mapper:
    def __init__(
        self,
        base_url: httpx.URL | str,
        data_source: str,
        flexible_attributes: FlexibleAttributes,
        ignore_video_tracks: bool,
        include_featured_album_artists: bool,
        language_preference: ContentLanguagePreference,
    ):
        self.base_url: str | httpx.URL = base_url
        self.data_source: str = data_source
        self.flexible_attributes: FlexibleAttributes = flexible_attributes
        self.ignore_video_tracks: bool = ignore_video_tracks
        self.include_featured_album_artists: bool = (
            include_featured_album_artists
        )
        self.lyrics_processor: LyricsProcessor = LyricsProcessor(
            language_preference=language_preference
        )

    def album_info(
        self,
        remote_album: AlbumForApiContract,
    ) -> AlbumInfo | None:
        """Convert VocaDB album API response to Beets AlbumInfo format.

        Args:
            remote_album: Album data from VocaDB API

        Returns:
            Album information in Beets format or None if conversion fails
        """
        if not remote_album.tracks:
            return
        remote_discs: tuple[AlbumDiscPropertiesContract, ...] = (
            remote_album.discs
            or discs_fallback(disc_total=remote_album.tracks[-1].disc_number)
        )
        album_genre: str | None = get_genres(
            remote_tags=remote_album.tags or ()
        )
        # track_genres: set[str | None] = set()
        tracks: list[TrackInfo]
        tracks = self.get_album_track_infos(
            remote_songs=remote_album.tracks,
            remote_discs=remote_discs,
            album_genre=album_genre,
        )
        remote_disc_type: DiscType
        va: bool = (
            remote_disc_type := remote_album.disc_type
        ) == DiscType.COMPILATION
        album: str | None = remote_album.name
        album_id: str = str(remote_album.id)
        artist: str
        artists: list[str]
        artists_ids: list[str]
        artist_id: str | None
        label: str | None
        artist, artist_id, artists, artists_ids, label = get_album_artists(
            remote_artists=remote_album.artists,
            include_featured_artists=self.include_featured_album_artists,
            comp=va,
        )
        if artist == VA_NAME:
            va = True
        asin: str | None = get_asin(web_links=remote_album.web_links)
        albumtype: str = remote_disc_type.lower()
        albumtypes: list[str] = [albumtype]
        remote_date: OptionalDateTimeContract = remote_album.release_date
        year: int | None = remote_date.year
        month: int | None = remote_date.month
        day: int | None = remote_date.day
        mediums: int = len(remote_discs)
        catalognum: str | None = remote_album.catalog_number
        media: str | None
        try:
            media = remote_discs[0].name
        except IndexError:
            media = None
        data_url: str = str(
            httpx.URL(url=self.base_url).join(url=f"Al/{album_id}")
        )
        album_info: AlbumInfo = AlbumInfo(
            tracks=tracks,
            album=album,
            # album_id=album_id,
            albumtype=albumtype,
            albumtypes=albumtypes,
            asin=asin,
            artist=artist,
            artists=artists,
            # artist_id=artist_id,
            artists_ids=artists_ids,
            catalognum=catalognum,
            data_source=self.data_source,
            day=day,
            label=label,
            media=media,
            mediums=mediums,
            month=month,
            va=va,
            year=year,
            data_url=data_url,
        )
        album_info.update(
            {
                self.flexible_attributes.album[
                    AlbumFlexibleAttributes.ALBUM_ID
                ]: album_id,
                self.flexible_attributes.album[
                    AlbumFlexibleAttributes.ALBUMARTIST_ID
                ]: artist_id,
                # self._flexible_attributes.album[
                #     AlbumFlexibleAttributes.ALBUMARTIST_IDS
                # ]: artists_ids,
            }
        )
        return album_info

    def get_album_track_infos(
        self,
        remote_songs: tuple[SongInAlbumForApiContract, ...],
        remote_discs: tuple[AlbumDiscPropertiesContract, ...],
        album_genre: str | None,
    ) -> list[TrackInfo]:
        """Extract track information from album data.

        Args:
            remote_songs: Track data from VocaDB API
            remote_discs: Disc data from VocaDB API
            album_genre: Default genre for tracks

        Returns:
            List of tracks in Beets TrackInfo format
        """
        remote_disc: AlbumDiscPropertiesContract
        remote_song: SongInAlbumForApiContract
        # track_genres: set[str | None] = set()
        tracks: list[TrackInfo] = []
        tracks_by_disc: dict[
            int,
            tuple[SongInAlbumForApiContract, ...],
        ] = group_tracks_by_disc(remote_songs=remote_songs)
        ignore_video_tracks: bool = self.ignore_video_tracks
        for disc_number, remote_disc_tracks in tracks_by_disc.items():
            if (
                not remote_disc_tracks
                or (remote_disc := remote_discs[disc_number - 1]).media_type
                == DiscMediaType.VIDEO
                and ignore_video_tracks
            ):
                continue
            track_info: TrackInfo | None
            total: int = len(remote_disc_tracks)
            for remote_song in remote_disc_tracks:
                if not remote_song.song or not (
                    track_info := self.track_info(
                        remote_song=remote_song.song,
                        index=remote_song.track_number,
                        media=remote_disc.name,
                        medium=disc_number,
                        medium_index=remote_song.track_number,
                        medium_total=total,
                    )
                ):
                    continue
                if not track_info.genre:
                    track_info.genre = album_genre

                tracks.append(track_info)
        return tracks

    def track_info(
        self,
        remote_song: SongForApiContract,
        index: int | None = None,
        media: str | None = None,
        medium: int | None = None,
        medium_index: int | None = None,
        medium_total: int | None = None,
    ) -> TrackInfo | None:
        """Convert VocaDB song API response to Beets TrackInfo format.

        Args:
            remote_song: Song data from VocaDB API
            index: Track index in album
            media: Media type (CD, Digital, etc.)
            medium: Disc number
            medium_index: Track number on disc
            medium_total: Total tracks on disc

        Returns:
            Track information in Beets TrackInfo format
        """
        artist: str
        artists: list[str]
        artists_ids: list[str]
        artist_id: str | None
        arranger: str | None
        composer: str | None
        lyricist: str | None
        (
            artist,
            artist_id,
            artists,
            artists_ids,
            arranger,
            composer,
            lyricist,
        ) = get_track_artists(remote_artists=remote_song.artists)
        track_id: str = str(remote_song.id)
        script: str | None
        language: str | None
        lyrics: str | None
        script, language, lyrics = self.lyrics_processor.get_lyrics(
            remote_lyrics_list=remote_song.lyrics,
        )
        original_day: int | None = None
        original_month: int | None = None
        original_year: int | None = None
        if remote_song.publish_date:
            date: datetime = remote_song.publish_date
            original_day = date.day
            original_month = date.month
            original_year = date.year
        track_info: TrackInfo = TrackInfo(
            title=remote_song.name,
            # track_id=track_id,
            artist=artist,
            artists=artists,
            # artist_id=artist_id,
            # artists_ids=artists_ids,
            length=remote_song.length_seconds,
            index=index,
            track_alt=str(index) if index else None,
            media=media,
            medium=medium,
            medium_index=medium_index,
            medium_total=medium_total,
            data_source=self.data_source,
            data_url=str(
                httpx.URL(url=self.base_url).join(url=f"S/{track_id}")
            ),
            lyricist=lyricist,
            composer=composer,
            arranger=arranger,
            bpm=get_bpm(remote_song.max_milli_bpm),
            genre=get_genres(remote_tags=remote_song.tags or ()),
            script=script,
            language=language,
            lyrics=lyrics,
            original_day=original_day,
            original_month=original_month,
            original_year=original_year,
        )
        track_info.update(
            {
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.TRACK_ID
                ]: track_id,
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.ARTIST_ID
                ]: artist_id,
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.ARTIST_IDS
                ]: artists_ids,
            }
        )
        return track_info
