from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from itertools import chain
from optparse import Values
from re import Match, match, search
from sys import version_info

from attrs import Attribute, Factory, define, fields
from typing_extensions import TypeAlias

if version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override
from urllib.parse import urljoin

from beets import autotag, config, library, ui, util
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from beets.autotag.match import track_distance
from beets.dbcore import types
from beets.library import Item, Library
from beets.plugins import BeetsPlugin, apply_item_changes, get_distance
from beets.ui import Subcommand, show_model_changes

from .plugin_config import InstanceConfig
from .requests_handler import SONG_FIELDS, RequestsHandler
from .requests_handler.models import (
    Album,
    AlbumArtist,
    AlbumFromQuery,
    AlbumQueryResult,
    Artist,
    Disc,
    Lyrics,
    ReleaseDate,
    Song,
    SongArtist,
    SongInAlbum,
    SongQueryResult,
    Tag,
    TagUsage,
    WebLink,
)

SongOrAlbumArtists: TypeAlias = "list[AlbumArtist] | list[SongArtist]"

NAME: str = __name__


@define
class FlexibleAttributes:
    album: frozenset[str]
    item: frozenset[str]

    def prefix(self, prefix: str) -> "FlexibleAttributes":
        prefixed_attributes: dict[str, frozenset[str]] = {}
        field: Attribute[frozenset[str]]
        for field in fields(self.__class__):
            attributes: frozenset[str] = getattr(self, field.name)
            prefixed_attributes[field.name] = frozenset(
                f"{prefix}_{attribute}" for attribute in attributes
            )
        return FlexibleAttributes(**prefixed_attributes)


@define
class ArtistsByCategories:
    producers: dict[str, str] = Factory(dict)
    circles: dict[str, str] = Factory(dict)
    vocalists: dict[str, str] = Factory(dict)
    arrangers: dict[str, str] = Factory(dict)
    composers: dict[str, str] = Factory(dict)
    lyricists: dict[str, str] = Factory(dict)


class VocaDBPlugin(BeetsPlugin):

    _requests_handler: type[RequestsHandler] = RequestsHandler
    _flexible_attributes: FlexibleAttributes = FlexibleAttributes(
        album=frozenset({"album_id", "artist_id"}),
        item=frozenset({"track_id", "artist_id"}),
    )
    _default_config: InstanceConfig = InstanceConfig()

    data_source: str = "VocaDB"
    subcommand: str = "vdbsync"

    languages: Iterable[str] | None = config["import"]["languages"].as_str_seq()

    def __init__(self) -> None:
        super().__init__()
        self.client: RequestsHandler = self._requests_handler(self._log)
        _prefixed_flex_attributes: FlexibleAttributes = (
            self._flexible_attributes.prefix(self.name)
        )
        self.album_types: dict[str, types.Integer] = {}
        self.item_types: dict[str, types.Integer] = {}
        field: Attribute[set[str]]
        for field in fields(_prefixed_flex_attributes.__class__):
            prefixed_attributes: str = getattr(_prefixed_flex_attributes, field.name)
            setattr(
                self,
                f"{field.name}_types",
                {
                    prefix_attribute: types.INTEGER
                    for prefix_attribute in prefixed_attributes
                },
            )
        self.config.add(
            {
                "source_weight": 0.5,
            }
        )
        self.instance_config: InstanceConfig = InstanceConfig.from_config_subview(
            self.config, self._default_config
        )
        self.language: str = self.get_lang()

    def __init_subclass__(
        cls, requests_handler: type[RequestsHandler], data_source: str, subcommand: str
    ) -> None:
        super().__init_subclass__()
        cls._requests_handler = requests_handler
        cls._default_config = InstanceConfig.from_config_subview(config[NAME])
        cls.data_source = data_source
        cls.subcommand = subcommand

    @override
    def commands(self) -> tuple[Subcommand, ...]:
        cmd: Subcommand = Subcommand(
            self.subcommand,
            help=f"update metadata from {self.data_source}",
        )
        cmd.parser.add_option(
            "-p",
            "--pretend",
            action="store_true",
            help="show all changes but do nothing",
        )
        cmd.parser.add_option(
            "-m",
            "--move",
            action="store_true",
            dest="move",
            help="move files in the library directory",
        )
        cmd.parser.add_option(
            "-M",
            "--nomove",
            action="store_false",
            dest="move",
            help="don't move files in library",
        )
        cmd.parser.add_option(
            "-W",
            "--nowrite",
            action="store_false",
            default=None,
            dest="write",
            help="don't write updated metadata to files",
        )
        cmd.parser.add_format_option()
        cmd.func = self.func
        return tuple([cmd])

    def func(self, lib: Library, opts: Values, args: list[str]) -> None:
        """Command handler for the *dbsync function."""
        move: bool = ui.should_move(opts.move)
        pretend: bool = opts.pretend
        write: bool = ui.should_write(opts.write)
        query: list[str] = ui.decargs(args)

        self.singletons(lib, query, move, pretend, write)
        self.albums(lib, query, move, pretend, write)

    def singletons(
        self, lib: Library, query: list[str], move: bool, pretend: bool, write: bool
    ) -> None:
        """Retrieve and apply info from the autotagger for items matched by
        query.
        """
        item: Item
        for item in lib.items(query + ["singleton:true"]):
            item_formatted: str = format(item)
            track_id: str | None = item.get("mb_trackid")
            if not track_id:
                self._log.debug(
                    "Skipping singleton with no mb_trackid: {0}",
                    item_formatted,
                )
                continue
            if not item.get("data_source") == self.data_source:
                self._log.debug(
                    "Skipping non-{0} singleton: {1}",
                    self.data_source,
                    item_formatted,
                )
                continue
            self._log.debug("Searching for track {0}", item.formatted())
            track_info: TrackInfo | None = self.track_for_id(track_id)
            if not (track_info):
                self._log.info(
                    "Recording ID not found: {0} for track {1}",
                    track_id,
                    item_formatted,
                )
                continue
            with lib.transaction():
                autotag.apply_item_metadata(item, track_info)
                show_model_changes(item)
                apply_item_changes(lib, item, move, pretend, write)

    def albums(
        self, lib: Library, query: list[str], move: bool, pretend: bool, write: bool
    ) -> None:
        """Retrieve and apply info from the autotagger for albums matched by
        query and their items.
        """
        album: library.Album
        for album in lib.albums(query):
            album_formatted: str = format(album)
            if not album.mb_albumid:
                self._log.debug(
                    "Skipping album with no mb_albumid: {0}",
                    album_formatted,
                )
                continue
            if not album.get("data_source") == self.data_source:
                self._log.debug(
                    "Skipping non-{0} album: {1}",
                    self.data_source,
                    album_formatted,
                )
                continue
            album_info: AlbumInfo | None = self.album_for_id(album.mb_albumid)
            if not (album_info):
                self._log.info(
                    "Release ID {0} not found for album {1}",
                    album.mb_albumid,
                    album_formatted,
                )
                continue
            items: Sequence[Item] = album.items()
            item: Item
            track_index: dict[str, TrackInfo] = {
                track.track_id: track for track in album_info.tracks if track.track_id
            }
            mapping: dict[Item, TrackInfo] = {}
            for item in items:
                if item.mb_trackid not in track_index:
                    old_track_id: str = item.mb_trackid
                    # Unset track id so that it won't affect distance
                    item.mb_trackid = None
                    matches: dict[str, Distance] = {
                        track_info.track_id: track_distance(item, track_info)
                        for track_info in track_index.values()
                        if track_info.track_id
                    }
                    item.mb_trackid = min(matches, key=lambda k: matches[k])
                    self._log.warning(
                        "Missing track ID {0} in album info for {1} automatched to ID {2}",
                        old_track_id,
                        album_formatted,
                        item.mb_trackid,
                    )
                mapping[item] = track_index[item.mb_trackid]

            self._log.debug("applying changes to {0}", album_formatted)
            with lib.transaction():
                autotag.apply_metadata(album_info, mapping)
                changed: bool = False
                any_changed_item: Item = items[0]
                for item in items:
                    item_changed: bool = show_model_changes(item)
                    changed |= item_changed
                    if item_changed:
                        any_changed_item = item
                        apply_item_changes(lib, item, move, pretend, write)
                if not changed:
                    continue
                if not pretend:
                    key: str
                    for key in library.Album.item_keys:
                        if key not in {
                            "original_day",
                            "original_month",
                            "original_year",
                            "genre",
                        }:
                            album[key] = any_changed_item[key]
                    album.store()
                    if move and lib.directory in util.ancestry(items[0].path):
                        self._log.debug("moving album {0}", album_formatted)
                        album.move()

    @override
    def track_distance(self, item: Item, info: TrackInfo) -> Distance:
        """Returns the track distance."""
        return get_distance(data_source=self.data_source, info=info, config=self.config)

    @override
    def album_distance(
        self,
        items: Iterable[Item],
        album_info: AlbumInfo,
        mapping: dict[Item, TrackInfo],
    ) -> Distance:
        """Returns the album distance."""
        return get_distance(
            data_source=self.data_source, info=album_info, config=self.config
        )

    @override
    def candidates(
        self,
        items: Iterable[Item],
        artist: str,
        album: str,
        va_likely: bool,
        extra_tags: dict[str, object] | None = None,
    ) -> tuple[()] | tuple[AlbumInfo, ...]:
        self._log.debug("Searching for album {0}", album)
        candidates_container: AlbumQueryResult | None = self.client._get(
            relative_path="albums",
            params={
                "query": album,
                "maxResults": str(self.instance_config.max_results),
                "nameMatchMode": "Auto",
            },
            cl=AlbumQueryResult,
        )
        if candidates_container:
            candidates: list[AlbumFromQuery] = candidates_container.items
            self._log.debug(
                "Found {0} result(s) for '{1}'",
                len(candidates),
                album,
            )
            # songFields parameter doesn't exist for album search
            # so we'll get albums by their id
            ids: list[str] = [str(album.id) for album in candidates]
            return tuple(map(self.album_for_id, ids))

        return ()

    @override
    def item_candidates(
        self, item: Item, artist: str, title: str
    ) -> tuple[TrackInfo, ...]:
        self._log.debug("Searching for track {0}", item)
        item_candidates_container: SongQueryResult | None = self.client._get(
            relative_path="songs",
            params={
                "query": title,
                "discTypes": "Album",
                "fields": SONG_FIELDS,
                "lang": self.language,
                "maxResults": str(self.instance_config.max_results),
                "nameMatchMode": "Auto",
                "preferAccurateMatches": "True",
                "sort": "SongType",
            },
            cl=SongQueryResult,
        )
        if item_candidates_container:
            items: list[Song] = item_candidates_container.items
            self._log.debug(
                "Found {0} result(s) for '{1}'",
                len(items),
                title,
            )
            return tuple(map(self.track_info, items))

        return ()

    def get_lang(self) -> str:
        """Used to set the 'language' instance attribute."""
        if not self.languages:
            return "English"

        lang: str
        for lang in self.languages:
            if lang == "jp":
                return "Romaji" if self.instance_config.prefer_romaji else "Japanese"
            if lang == "en":
                return "English"

        return "English"  # Default if no matching language found

    @override
    def album_for_id(self, album_id: str) -> AlbumInfo | None:
        if not album_id.isnumeric():
            self._log.debug(
                "Skipping non-{0} album: {1}",
                self.data_source,
                album_id,
            )
            return None
        self._log.debug("Searching for album {0}", album_id)
        album: Album | None = self.client._get(
            relative_path=f"albums/{album_id}",
            params={
                "lang": self.language,
                "fields": "Artists,Discs,Tags,Tracks,WebLinks",
                "songFields": SONG_FIELDS,
            },
            cl=Album,
        )
        return self.album_info(album, search_lang=self.language) if album else None

    @override
    def track_for_id(self, track_id: str) -> TrackInfo | None:
        if not track_id.isnumeric():
            self._log.debug(
                "Skipping non-{0} singleton: {1}",
                self.data_source,
                track_id,
            )
            return None
        self._log.debug("Searching for track {0}", track_id)
        track: Song | None = self.client._get(
            relative_path=f"songs/{track_id}",
            params={
                "lang": self.language,
                "fields": SONG_FIELDS,
            },
            cl=Song,
        )
        return self.track_info(track, search_lang=self.language) if track else None

    def album_info(
        self, release: Album, search_lang: str | None = None
    ) -> AlbumInfo:
        if not release.discs:
            release.discs = [
                Disc(discNumber=i + 1, name="CD", mediaType="Audio")
                for i in range(max(track.discNumber for track in release.tracks))
            ]
        ignored_discs: set[int] = set()
        disc: Disc
        for disc in release.discs:
            disc_number: int = disc.discNumber
            if (
                disc.mediaType == "Video"
                and config["match"]["ignore_video_tracks"].get(bool)
                or not release.tracks
            ):
                ignored_discs.add(disc_number)
            else:
                disc.total = max(
                    {
                        track.trackNumber
                        for track in release.tracks
                        if track.discNumber == disc_number
                    }
                )

        va: bool = release.discType == "Compilation"
        album: str | None = release.name
        album_id: str | None = str(release.id)
        artist_categories: ArtistsByCategories
        artist: str
        artist_categories, artist = self.get_artists(
            release.artists,
            include_featured_artists=self.instance_config.include_featured_album_artists,
            comp=va,
        )
        if artist == config["va_name"].as_str():
            va = True
        # for membership checks in constant time
        artists_set: set[str] = set()
        artists_ids_set: set[str] = set()
        artists: list[str] = []
        artists_ids: list[str] = []
        field: Attribute[dict[str, str]]
        for field in fields(artist_categories.__class__):
            category: dict[str, str] = getattr(artist_categories, field.name)
            keys: list[str] = list(category.keys())
            values: list[str] = list(category.values())

            # Filter keys and values before updating the sets
            new_artists: list[str] = list(
                filter(lambda artist: artist not in artists_set, keys)
            )
            new_artists_ids: list[str] = list(
                filter(lambda artist_id: artist_id not in artists_ids_set, values)
            )

            artists.extend(new_artists)
            artists_ids.extend(new_artists_ids)

            # Update the sets after filtering
            artists_set.update(new_artists)
            artists_ids_set.update(new_artists_ids)
        artist_id: str | None
        try:
            artist_id = artists_ids[0]
        except IndexError:
            artist_id = None
        tracks: list[TrackInfo]
        script: str | None
        language: str | None
        tracks, script, language = self.get_album_track_infos(
            release.tracks,
            release.discs,
            ignored_discs,
            search_lang,
        )
        weblink: WebLink
        asin: str | None = None
        for weblink in release.webLinks:
            if not weblink.disabled and match(
                "Amazon( \\((LE|RE|JP|US)\\).*)?$", weblink.description
            ):
                asin_match: Match[str] | None = search(
                    "\\/dp\\/(.+?)(\\/|$)", weblink.url
                )
                if asin_match:
                    asin = asin_match[1]
                    break
        albumtype: str | None = release.discType
        albumtypes: list[str] | None = None
        if albumtype:
            albumtype = albumtype.lower()
            albumtypes = [albumtype]
        date: ReleaseDate | None = release.releaseDate
        year: int | None
        month: int | None
        day: int | None
        if date and not date.isEmpty:
            year = date.year
            month = date.month
            day = date.day
        else:
            year = month = day = None
        label: str | None = None
        albumartist: AlbumArtist
        for albumartist in release.artists:
            if "Label" in albumartist.categories:
                label = albumartist.name
                break
        discs: Sequence[Disc] = release.discs
        mediums: int = len(discs)
        catalognum: str | None = release.catalogNumber
        genre: str | None = self.get_genres(release.tags)
        media: str | None
        try:
            media = discs[0].name
        except IndexError:
            media = None
        data_url: str = urljoin(self.client.base_url, f"Al/{album_id}")
        return AlbumInfo(
            album=album,
            album_id=album_id,
            artist=artist,
            artists=artists,
            artist_id=artist_id,
            artists_ids=artists_ids,
            tracks=tracks,
            asin=asin,
            albumtype=albumtype,
            albumtypes=albumtypes,
            va=va,
            year=year,
            month=month,
            day=day,
            label=label,
            mediums=mediums,
            catalognum=catalognum,
            script=script,
            language=language,
            genre=genre,
            media=media,
            data_source=self.data_source,
            data_url=data_url,
        )

    def track_info(
        self,
        recording: Song,
        index: int | None = None,
        media: str | None = None,
        medium: int | None = None,
        medium_index: int | None = None,
        medium_total: int | None = None,
        search_lang: str | None = None,
    ) -> TrackInfo:
        title: str = recording.name
        track_id: str = str(recording.id)
        artist_categories: ArtistsByCategories
        artist: str
        artist_categories, artist = self.get_artists(recording.artists)
        # for membership checks in constant time
        artists_set: set[str] = set()
        artists_ids_set: set[str] = set()
        artists: list[str] = []
        artists_ids: list[str] = []
        field: Attribute[dict[str, str]]
        category: dict[str, str]
        for field in fields(artist_categories.__class__):
            category = getattr(artist_categories, field.name)
            keys: list[str] = list(category.keys())
            values: list[str] = list(category.values())

            # Filter keys and values before updating the sets
            new_artists: list[str] = list(
                filter(lambda artist: artist not in artists_set, keys)
            )
            new_artists_ids: list[str] = list(
                filter(lambda artist_id: artist_id not in artists_ids_set, values)
            )

            artists.extend(new_artists)
            artists_ids.extend(new_artists_ids)

            # Update the sets after filtering
            artists_set.update(new_artists)
            artists_ids_set.update(new_artists_ids)
        artist_id: str | None
        try:
            artist_id = artists_ids[0]
        except IndexError:
            artist_id = None
        arranger: str = ", ".join(artist_categories.arrangers)
        composer: str = ", ".join(artist_categories.composers)
        lyricist: str = ", ".join(artist_categories.lyricists)
        length: float = recording.lengthSeconds
        data_url: str = urljoin(self.client.base_url, f"S/{track_id}")
        max_milli_bpm: int | None = recording.maxMilliBpm
        bpm: str | None = str(max_milli_bpm // 1000) if max_milli_bpm else None
        genre: str | None = self.get_genres(recording.tags)
        script: str | None
        language: str | None
        lyrics: str | None
        script, language, lyrics = self.get_lyrics(
            recording.lyrics,
            search_lang,
        )
        original_day: int | None = None
        original_month: int | None = None
        original_year: int | None = None
        if recording.publishDate:
            date: datetime = datetime.fromisoformat(recording.publishDate[:-1])
            original_day = date.day
            original_month = date.month
            original_year = date.year
        return TrackInfo(
            title=title,
            track_id=track_id,
            artist=artist,
            artists=artists,
            artist_id=artist_id,
            artists_ids=artists_ids,
            length=length,
            index=index,
            track_alt=str(index) if index is not None else None,
            media=media,
            medium=medium,
            medium_index=medium_index,
            medium_total=medium_total,
            data_source=self.data_source,
            data_url=data_url,
            lyricist=lyricist,
            composer=composer,
            arranger=arranger,
            bpm=bpm,
            genre=genre,
            script=script,
            language=language,
            lyrics=lyrics,
            original_day=original_day,
            original_month=original_month,
            original_year=original_year,
        )

    def get_album_track_infos(
        self,
        tracks: list[SongInAlbum],
        discs: Sequence[Disc],
        ignored_discs: set[int],
        search_lang: str | None,
    ) -> tuple[list[TrackInfo], str | None, str | None]:
        track_infos: list[TrackInfo] = []
        script: str | None = None
        language: str | None = None
        index: int
        track: SongInAlbum
        for index, track in enumerate(tracks):
            disc_number: int | None = track.discNumber
            if disc_number in ignored_discs or not track.song:
                continue
            format: str | None = discs[disc_number - 1].name
            total: int | None = discs[disc_number - 1].total
            track_info: TrackInfo = self.track_info(
                recording=track.song,
                index=index + 1,
                media=format,
                medium=disc_number,
                medium_index=track.trackNumber,
                medium_total=total,
                search_lang=search_lang,
            )
            if track_info.script and script != "Qaaa":
                if not script:
                    script = track_info.script
                    language = track_info.language
                elif script != track_info.script:
                    script = "Qaaa"
                    language = "mul"
            track_infos.append(track_info)
        if script == "Qaaa" or language == "mul":
            for track_info in track_infos:
                track_info.script = script
                track_info.language = language
        return track_infos, script, language

    def get_artists(
        self,
        artists: SongOrAlbumArtists,
        include_featured_artists: bool = True,
        comp: bool = False,
    ) -> tuple[ArtistsByCategories, str]:
        artists_by_categories: ArtistsByCategories
        support_artists: set[str]

        artists_by_categories, support_artists = self.get_artists_by_categories(artists)
        va_name: str = config["va_name"].as_str()

        main_artists: list[str] = (
            [va_name]
            if comp
            else [
                name
                for name in chain(
                    artists_by_categories.producers.keys(),
                    artists_by_categories.circles.keys(),
                )
                if name not in support_artists
            ]
        )

        artist_string: str = (
            ", ".join(main_artists) if not len(main_artists) > 5 else va_name
        )

        if (
            include_featured_artists
            and artists_by_categories.vocalists
            and (comp or main_artists)
        ):
            featured_artists: list[str] = [
                name
                for name in artists_by_categories.vocalists.keys()
                if name not in support_artists
            ]
            if featured_artists and not len(main_artists) + len(featured_artists) > 5:
                artist_string += " feat. " + ", ".join(featured_artists)

        return artists_by_categories, artist_string

    @staticmethod
    def get_artists_by_categories(
        artists: SongOrAlbumArtists,
    ) -> tuple[ArtistsByCategories, set[str]]:
        artists_by_categories: ArtistsByCategories = ArtistsByCategories()
        support_artists: set[str] = set()
        artist: AlbumArtist | SongArtist
        for artist in artists:
            parent: Artist | None = artist.artist
            name: str
            id: str
            if parent:
                name = parent.name
                id = str(parent.id)
            else:
                name = artist.name
                id = ""
            if artist.isSupport:
                support_artists.add(name)
            if "Producer" in artist.categories or "Band" in artist.categories:
                if "Default" in artist.effectiveRoles:
                    artist.effectiveRoles += ",Arranger,Composer,Lyricist"
                artists_by_categories.producers[name] = id
            if "Circle" in artist.categories:
                artists_by_categories.circles[name] = id
            if "Arranger" in artist.effectiveRoles:
                artists_by_categories.arrangers[name] = id
            if "Composer" in artist.effectiveRoles:
                artists_by_categories.composers[name] = id
            if "Lyricist" in artist.effectiveRoles:
                artists_by_categories.lyricists[name] = id
            if "Vocalist" in artist.categories:
                artists_by_categories.vocalists[name] = id
        if not artists_by_categories.producers and artists_by_categories.vocalists:
            artists_by_categories.producers = artists_by_categories.vocalists
        if not artists_by_categories.arrangers:
            artists_by_categories.arrangers = artists_by_categories.producers
        if not artists_by_categories.composers:
            artists_by_categories.composers = artists_by_categories.producers
        if not artists_by_categories.lyricists:
            artists_by_categories.lyricists = artists_by_categories.producers
        return artists_by_categories, support_artists

    @staticmethod
    def get_genres(tags: list[TagUsage]) -> str | None:
        genres: list[str] = []
        tag_usage: TagUsage
        for tag_usage in sorted(tags, reverse=True, key=lambda x: x.count):
            tag: Tag = tag_usage.tag
            if tag.categoryName == "Genres":
                tag_name: str | None = tag.name
                if tag_name:
                    genres.append(tag_name.title())
        return "; ".join(genres) if genres else None

    @classmethod
    def get_lyrics(
        cls,
        lyrics: list[Lyrics],
        language: str | None = None,
        translated_lyrics: bool = False,
    ) -> tuple[str | None, str | None, str | None]:
        out_script: str | None = None
        out_language: str | None = None
        out_lyrics: str | None = None
        lyric: Lyrics
        for lyric in lyrics:
            translation_type: str = lyric.translationType
            value: str = lyric.value
            culture_codes: set[str] = set(lyric.cultureCodes) & {"en", "ja"}
            if culture_codes:
                if "en" in culture_codes:
                    if translation_type == "Original":
                        out_script = "Latn"
                        out_language = "eng"
                    if translated_lyrics or language == "English":
                        out_lyrics = value
                elif "ja" in culture_codes:
                    if translation_type == "Original":
                        out_script = "Jpan"
                        out_language = "jpn"
                    if not translated_lyrics and language == "Japanese":
                        out_lyrics = value
            if (
                not translated_lyrics
                and language == "Romaji"
                and translation_type == "Romanized"
            ):
                out_lyrics = value
        if not out_lyrics and lyrics:
            out_lyrics = cls.get_fallback_lyrics(lyrics, language)
        return out_script, out_language, out_lyrics

    @staticmethod
    def get_fallback_lyrics(
        lyrics: list[Lyrics], language: str | None
    ) -> str | None:
        lyric: Lyrics
        if language == "English":
            for lyric in lyrics:
                if "en" in lyric.cultureCodes:
                    return lyric.value
            language = "Romaji"
        if language == "Romaji":
            for lyric in lyrics:
                if lyric.translationType == "Romanized":
                    return lyric.value
        return lyrics[0].value if lyrics else None
