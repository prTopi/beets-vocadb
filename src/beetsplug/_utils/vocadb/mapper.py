from __future__ import annotations

import posixpath
from enum import auto
from logging import Logger
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from beets.autotag.hooks import AlbumInfo, TrackInfo

from .artists import ArtistsProcessor
from .lyrics import LyricsProcessor
from .utils import (
    discs_fallback,
    get_asin,
    get_genres,
    group_tracks_by_disc,
    normalize_bpm,
)
from .vocadb_api_client import (
    ArtistApiApi,
    ContentLanguagePreference,
    DiscMediaType,
    DiscType,
    SongOptionalFields,
    SongOptionalFieldsSet,
    SongType,
    TagApiApi,
)
from .vocadb_api_client.models import StrEnum

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Sequence
    from datetime import datetime

    from .vocadb_api_client import (
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
    ARRANGER_IDS = auto()
    COMPOSER_IDS = auto()
    LYRICIST_IDS = auto()
    REMIXER_IDS = auto()


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
        base_url: str,
        data_source: str,
        flexible_attributes: FlexibleAttributes,
        ignore_video_tracks: bool,
        artist_api: ArtistApiApi,
        song_api: SongApiApi,
        tag_api: TagApiApi,
        language_preference: ContentLanguagePreference,
        include_featured_album_artists: bool,
        use_base_voicebank: bool,
        exclude_item_fields: list[str],
        exclude_album_fields: list[str],
        va_name: str,
        logger: Logger,
    ) -> None:
        self.base_url: str = base_url
        self.data_source: str = data_source
        self.flexible_attributes: FlexibleAttributes = flexible_attributes
        self.ignore_video_tracks: bool = ignore_video_tracks
        self.artists_processor: ArtistsProcessor = ArtistsProcessor(
            va_name=va_name,
            artist_api=artist_api,
            tag_api=tag_api,
            use_base_voicebank=use_base_voicebank,
            language_preference=language_preference,
            logger=logger,
        )
        self.lyrics_processor: LyricsProcessor = LyricsProcessor(
            language_preference=language_preference,
        )
        self.include_featured_album_artists: bool = (
            include_featured_album_artists
        )
        self.use_base_voicebank: bool = use_base_voicebank
        self.exclude_item_fields: list[str] = exclude_item_fields
        self.exclude_album_fields: list[str] = exclude_album_fields
        self.song_api: SongApiApi = song_api
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
        remote_discs: Sequence[AlbumDiscPropertiesContract] = (
            remote_album.discs
            or discs_fallback(disc_total=remote_album.tracks[-1].disc_number)
        )
        album_genres: list[str] | None = get_genres(
            remote_tags=remote_album.tags
        )
        # track_genres: set[str | None] = set()
        tracks: list[TrackInfo]
        tracks = self.get_album_track_infos(
            remote_songs=remote_album.tracks,
            remote_discs=remote_discs,
            album_genres=album_genres,
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
                include_featured_artists=self.include_featured_album_artists,
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
        data_url: str = urljoin(
            base=self.base_url, url=posixpath.join("Al", album_id)
        )
        cover_art_url: str | None = (
            remote_main_picture.url_original
            if (remote_main_picture := remote_album.main_picture)
            else None
        )
        album_info: AlbumInfo = AlbumInfo(
            tracks=tracks,
            album=album,
            album_id=None,
            albumtype=albumtype,
            albumtypes=albumtypes,
            asin=asin,
            artist=artist,
            artists=artists,
            # artist_id=artist_id,
            # artists_ids=artists_ids,
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
            albumdisambig=None,
            albumstatus=None,
            barcode=None,
            country=None,
            discogs_albumid=None,
            discogs_artistid=None,
            discogs_labelid=None,
            language=None,
            release_group_title=None,
            releasegroup_id=None,
            releasegroupdisambig=None,
            script=None,
            style=None,
            **{
                self.flexible_attributes.album[
                    AlbumFlexibleAttributes.ALBUM_ID
                ]: album_id,
                self.flexible_attributes.album[
                    AlbumFlexibleAttributes.ALBUMARTIST_ID
                ]: artist_id,
                # upstream fix pending:
                # self.flexible_attributes.album[
                #     AlbumFlexibleAttributes.ALBUMARTIST_IDS
                # ]: artists_ids,
            },
        )
        for field in self.exclude_album_fields:
            del album_info[field]
        return album_info

    def get_album_track_infos(
        self,
        remote_songs: Iterable[SongInAlbumForApiContract],
        remote_discs: Sequence[AlbumDiscPropertiesContract],
        album_genres: list[str] | None,
    ) -> list[TrackInfo]:
        """Extract track information from album data.

        Args:
            remote_songs: Track data from VocaDB API
            remote_discs: Disc data from VocaDB API
            album_genres: Default genres for tracks

        Returns:
            List of tracks in Beets TrackInfo format
        """
        remote_disc: AlbumDiscPropertiesContract
        remote_song: SongInAlbumForApiContract
        # track_genres: set[str | None] = set()
        tracks: list[TrackInfo] = []
        tracks_by_disc: dict[
            int,
            Collection[SongInAlbumForApiContract],
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
                if not track_info.genres:
                    track_info.genres = album_genres

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
        remote_artists: tuple[ArtistForSongContract, ...] | None = (
            remote_song.artists
        )
        remote_original_version_id: int | None
        remote_derivate_song: SongForApiContract = remote_song
        while (
            remote_original_version_id
            := remote_derivate_song.original_version_id
        ):
            # logic for derived songs
            self._log.debug(
                msg=f'Track "{remote_derivate_song.name}" with id '
                + f"{remote_derivate_song.id} is a derivative of "
                + f"the track with id {remote_original_version_id}."
            )
            remote_original_song: SongForApiContract | None = (
                self.song_api.api_songs_id_get(
                    id=remote_original_version_id,
                    fields=SongOptionalFieldsSet((SongOptionalFields.ARTISTS,)),
                    lang=self.language_preference,
                )
            )
            if not remote_original_song:
                return None
            if remote_original_song.original_version_id:
                remote_derivate_song = remote_original_song
                continue
            remote_original_artists: (
                tuple[ArtistForSongContract, ...] | None
            ) = remote_original_song.artists if remote_original_song else None
            break

        else:
            remote_original_artists = None
        artist: str
        artist_id: str | None
        artists: list[str]
        artist_ids: list[str]
        arrangers: list[str] | None
        arranger_ids: list[str] | None
        composers: list[str] | None
        composer_ids: list[str] | None
        lyricists: list[str] | None
        lyricist_ids: list[str] | None
        (
            artist,
            artist_id,
            artists,
            artist_ids,
            arrangers,
            arranger_ids,
            composers,
            composer_ids,
            lyricists,
            lyricist_ids,
        ) = self.artists_processor.get_track_artists(
            remote_artists=remote_artists,
            remote_original_artists=remote_original_artists,
        )
        remixers: list[str] | None
        remixers_ids: list[str] | None
        remixers, remixers_ids = (
            (arrangers, arranger_ids)
            if remote_song.song_type is SongType.REMIX
            else (None, None)
        )
        track_id: str = str(remote_song.id)
        script: str | None
        language: str | None
        lyrics: str | None
        script, language, lyrics = self.lyrics_processor.get_lyrics(
            remote_lyrics=remote_song.lyrics,
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
            data_url=urljoin(
                base=self.base_url, url=posixpath.join("S", track_id)
            ),
            lyricists=lyricists,
            lyricists_ids=None,
            composers=composers,
            composers_ids=None,
            arrangers=arrangers,
            arrangers_ids=None,
            remixers=remixers,
            remixers_ids=None,
            bpm=normalize_bpm(milli_bpm=remote_song.max_milli_bpm),
            genres=get_genres(remote_tags=remote_song.tags),
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
                ]: artist_ids,
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.ARRANGER_IDS
                ]: arranger_ids,
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.COMPOSER_IDS
                ]: composer_ids,
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.LYRICIST_IDS
                ]: lyricist_ids,
                self.flexible_attributes.item[
                    ItemFlexibleAttributes.REMIXER_IDS
                ]: remixers_ids,
            },
        )
        for field in self.exclude_item_fields:
            del track_info[field]
        return track_info
