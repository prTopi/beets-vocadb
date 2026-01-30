from __future__ import annotations

from enum import auto
from logging import Logger
from typing import TYPE_CHECKING

import httpx
from beets.autotag.hooks import AlbumInfo, TrackInfo
from confuse import ConfigView

from beetsplug.vocadb.artists import ArtistsProcessor
from beetsplug.vocadb.lyrics import LyricsProcessor
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
)
from beetsplug.vocadb.vocadb_api_client.models import StrEnum
from beetsplug.vocadb.vocadb_api_client.models.song_optional_fields import (
    SongOptionalFields,
    SongOptionalFieldsSet,
)

if TYPE_CHECKING:
    from datetime import datetime

    from beetsplug.vocadb.vocadb_api_client import (
        AlbumApiApi,
        AlbumDiscPropertiesContract,
        AlbumForApiContract,
        ArtistForSongContract,
        OptionalDateTimeContract,
        SongApiApi,
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
        album_api: AlbumApiApi,
        song_api: SongApiApi,
        config: ConfigView,
        language_preference: ContentLanguagePreference,
        va_name: str,
        logger: Logger,
    ) -> None:
        self.base_url: str | httpx.URL = base_url
        self.data_source: str = data_source
        self.flexible_attributes: FlexibleAttributes = flexible_attributes
        self.ignore_video_tracks: bool = ignore_video_tracks
        self.artists_processor: ArtistsProcessor = ArtistsProcessor(
            va_name=va_name
        )
        self.lyrics_processor: LyricsProcessor = LyricsProcessor(
            language_preference=language_preference
        )
        self.album_api: AlbumApiApi = album_api
        self.song_api: SongApiApi = song_api
        self.config: ConfigView = config
        self.language_preference: ContentLanguagePreference = (
            language_preference
        )
        self._log: Logger = logger

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
            return None
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
        artist, artist_id, artists, artists_ids, label = (
            self.artists_processor.get_album_artists(
                remote_artists=remote_album.artists,
                include_featured_artists=self.config[
                    "include_featured_album_artists"
                ].get(bool),
                comp=va,
            )
        )
        if artist == self.artists_processor.va_name:
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
        cover_art_url: str | None = (
            remote_main_picture.url_original
            if (remote_main_picture := remote_album.main_picture)
            else None
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
            cover_art_url=cover_art_url,
            original_day=None,
            original_month=None,
            original_year=None,
            **{
                self.flexible_attributes.album[
                    AlbumFlexibleAttributes.ALBUM_ID
                ]: album_id,
                self.flexible_attributes.album[
                    AlbumFlexibleAttributes.ALBUMARTIST_ID
                ]: artist_id,
                # self._flexible_attributes.album[
                #     AlbumFlexibleAttributes.ALBUMARTIST_IDS
                # ]: artists_ids,
            },
        )
        for field in self.config["exclude_album_fields"].as_str_seq():
            del album_info[field]
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
                        media=remote_disc.name,  # pyrefly: ignore[unbound-name]
                        medium=disc_number,
                        medium_index=remote_song.track_number,
                        medium_total=total,
                    )
                ):
                    continue
                if not track_info.genre:  # pyrefly: ignore[unbound-name]
                    track_info.genre = (  # pyrefly: ignore[unbound-name]
                        album_genre
                    )

                tracks.append(track_info)  # pyrefly: ignore[unbound-name]
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
        remote_artists: tuple[ArtistForSongContract, ...] | None = (
            remote_song.artists
        )
        remote_original_version_id: int | None
        if remote_original_version_id := remote_song.original_version_id:
            # logic for derived songs
            self._log.debug(
                msg=f'Track "{remote_song.name}" with id '
                + f"{remote_song.id} is a derivate of "
                + f"a the track with id {remote_original_version_id}."
            )
            remote_original_song: SongForApiContract | None = (
                self.song_api.api_songs_id_get(
                    id=remote_original_version_id,
                    fields=SongOptionalFieldsSet(  # pyrefly: ignore[no-matching-overload] # noqa: E501
                        (SongOptionalFields.ARTISTS,)
                    ),
                    lang=self.language_preference,
                )
            )
            if not remote_original_song:
                return None
            remote_original_artists: (
                tuple[ArtistForSongContract, ...] | None
            ) = remote_original_song.artists if remote_original_song else None

        else:
            remote_original_artists = None
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
        ) = self.artists_processor.get_track_artists(
            remote_artists=remote_artists,
            remote_original_artists=remote_original_artists,
        )
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
            track_id=None,
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
            composer_sort=None,
            disctitle=None,
            initial_key=None,
            mb_workid=None,
            release_track_id=None,
            work=None,
            work_disambig=None,
            **{
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.TRACK_ID
                ]: track_id,
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.ARTIST_ID
                ]: artist_id,
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.ARTIST_IDS
                ]: artists_ids,
            },
        )
        for field in self.config["exclude_item_fields"].as_str_seq():
            del track_info[field]
        return track_info
