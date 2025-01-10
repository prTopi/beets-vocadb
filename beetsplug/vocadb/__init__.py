from __future__ import annotations

import sys
from re import match, search
from typing import TYPE_CHECKING

import msgspec

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override
from urllib.parse import urljoin

from beets import __version__ as beets_version
from beets import autotag, config, dbcore, library, ui, util
from beets.autotag.hooks import AlbumInfo, TrackInfo
from beets.autotag.match import track_distance
from beets.plugins import BeetsPlugin, apply_item_changes, get_distance
from beets.ui import Subcommand, show_model_changes

from .plugin_config import InstanceConfig
from .requests_handler import RequestsHandler
from .requests_handler.models import (
    Album,
    AlbumQueryResult,
    ArtistCategories,
    ArtistRoles,
    Disc,
    DiscMediaType,
    DiscTypes,
    Song,
    SongQueryResult,
    TranslationType,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from datetime import datetime
    from optparse import Values
    from re import Match

    from beets.autotag.hooks import Distance
    from beets.library import Library
    from typing_extensions import LiteralString, TypeAlias

    from .requests_handler.models import (
        AlbumArtist,
        AlbumFromQuery,
        Lyrics,
        ReleaseDate,
        SongArtist,
        SongInAlbum,
        Tag,
        TagUsage,
        WebLink,
    )


SongOrAlbumArtists: TypeAlias = "list[AlbumArtist] | list[SongArtist]"

NAME: str = __name__
USER_AGENT: str = f"beets/{beets_version} +https://beets.io/"
SONG_FIELDS: LiteralString = "Artists,CultureCodes,Tags,Bpm,Lyrics"


class FlexibleAttributes(
    msgspec.Struct, forbid_unknown_fields=True, omit_defaults=True
):
    album: frozenset[str]
    item: frozenset[str]

    def with_prefix(self, prefix: str) -> FlexibleAttributes:
        """Add prefix to all attributes in each field.

        Args:
            prefix: String prefix to add to attribute names

        Returns:
            New FlexibleAttributes instance with prefixed attributes
        """

        def add_prefix(attrs: frozenset[str]) -> frozenset[str]:
            return frozenset(f"{prefix}_{attr}" for attr in attrs)

        return FlexibleAttributes(
            album=add_prefix(self.album), item=add_prefix(self.item)
        )


class ArtistsByCategories(
    msgspec.Struct, forbid_unknown_fields=True, omit_defaults=True
):
    producers: dict[str, str] = {}
    circles: dict[str, str] = {}
    vocalists: dict[str, str] = {}
    arrangers: dict[str, str] = {}
    composers: dict[str, str] = {}
    lyricists: dict[str, str] = {}


class VocaDBPlugin(BeetsPlugin):
    _requests_handler: type[RequestsHandler] = RequestsHandler
    _flexible_attributes: FlexibleAttributes = FlexibleAttributes(
        album=frozenset({"album_id", "artist_id"}),
        item=frozenset({"track_id", "artist_id"}),
    )
    _default_config: InstanceConfig = InstanceConfig()

    data_source: str = "VocaDB"
    base_url: str = "https://vocadb.net/"
    subcommand: str = "vdbsync"

    languages: Iterable[str] | None = config["import"]["languages"].as_str_seq()

    def __init__(self) -> None:
        super().__init__()
        self.client: RequestsHandler = self._requests_handler(
            USER_AGENT, self._log
        )
        _prefixed_flex_attributes: FlexibleAttributes = (
            self._flexible_attributes.with_prefix(self.name)
        )
        self.album_types: dict[str, dbcore.types.Integer] = {
            prefix_attribute: dbcore.types.INTEGER
            for prefix_attribute in _prefixed_flex_attributes.album
        }
        self.item_types: dict[str, dbcore.types.Integer] = {
            prefix_attribute: dbcore.types.INTEGER
            for prefix_attribute in _prefixed_flex_attributes.item
        }
        self.config.add(
            {
                "source_weight": 0.5,
            }
        )
        self.instance_config: InstanceConfig = (
            InstanceConfig.from_config_subview(
                self.config, self._default_config
            )
        )
        self.language: str = self.get_lang()

    def __init_subclass__(
        cls,
        requests_handler: type[RequestsHandler],
        data_source: str,
        base_url: str,
        subcommand: str,
    ) -> None:
        super().__init_subclass__()
        cls._requests_handler = requests_handler
        cls._default_config = InstanceConfig.from_config_subview(config[NAME])
        cls.data_source = data_source
        cls.base_url = base_url
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
        self,
        lib: Library,
        query: list[str],
        move: bool,
        pretend: bool,
        write: bool,
    ) -> None:
        """Retrieve and apply info from the autotagger for items matched by
        query.
        """
        item: library.Item
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
            self._log.debug("Searching for track {0}", item_formatted)
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
        self,
        lib: Library,
        query: list[str],
        move: bool,
        pretend: bool,
        write: bool,
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
            items: Sequence[library.Item] = album.items()
            item: library.Item
            track_index: dict[str, TrackInfo] = {
                track_id: track
                for track in album_info.tracks
                if (track_id := track.track_id)
            }
            mapping: dict[library.Item, TrackInfo] = {}
            for item in items:
                try:
                    mapping[item] = track_index[item.mb_trackid]
                except IndexError:
                    old_track_id: str = item.mb_trackid
                    # Unset track id so that it won't affect distance
                    item.mb_trackid = None
                    matches: dict[str, Distance] = {
                        track_id: track_distance(item, track_info)
                        for track_info in track_index.values()
                        if (track_id := track_info.track_id)
                    }
                    item.mb_trackid = min(matches, key=lambda k: matches[k])
                    self._log.warning(
                        "Missing track ID {0} in album info for {1} "
                        "automatched to ID {2}",
                        old_track_id,
                        album_formatted,
                        item.mb_trackid,
                    )

            self._log.debug("applying changes to {0}", album_formatted)
            with lib.transaction():
                autotag.apply_metadata(album_info, mapping)
                changed: bool = False
                any_changed_item: library.Item = items[0]
                for item in items:
                    item_changed: bool = show_model_changes(item)
                    changed |= item_changed
                    if item_changed:
                        any_changed_item = item
                        apply_item_changes(lib, item, move, pretend, write)
                if pretend or not changed:
                    continue
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
    def track_distance(self, item: library.Item, info: TrackInfo) -> Distance:
        """Returns the track distance."""
        return get_distance(
            data_source=self.data_source, info=info, config=self.config
        )

    @override
    def album_distance(
        self,
        items: Iterable[library.Item],
        album_info: AlbumInfo,
        mapping: dict[library.Item, TrackInfo],
    ) -> Distance:
        """Returns the album distance."""
        return get_distance(
            data_source=self.data_source, info=album_info, config=self.config
        )

    @override
    def candidates(
        self,
        items: Iterable[library.Item],
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
            type=AlbumQueryResult,
        )
        if not candidates_container:
            return ()
        candidates: list[AlbumFromQuery] = candidates_container.items
        self._log.debug(
            "Found {0} result(s) for '{1}'",
            len(candidates),
            album,
        )
        # songFields parameter doesn't exist for album search
        # so we'll get albums by their id
        return tuple(
            info
            for id in [str(album.id) for album in candidates]
            if (info := self.album_for_id(id))
        )

    @override
    def item_candidates(
        self, item: library.Item, artist: str, title: str
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
            type=SongQueryResult,
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
                return (
                    "Romaji"
                    if self.instance_config.prefer_romaji
                    else "Japanese"
                )
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
            type=Album,
        )
        return (
            self.album_info(album, search_lang=self.language) if album else None
        )

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
            type=Song,
        )
        return (
            self.track_info(track, search_lang=self.language) if track else None
        )

    def album_info(
        self, release: Album, search_lang: str | None = None
    ) -> AlbumInfo:
        if not release.discs:
            release.discs = [
                Disc(
                    disc_number=i + 1, name="CD", media_type=DiscMediaType.AUDIO
                )
                for i in range(
                    max(track.disc_number for track in release.tracks)
                )
            ]
        ignored_discs: set[int] = set()
        disc: Disc
        for disc in release.discs:
            disc_number: int = disc.disc_number
            if (
                disc.media_type == DiscMediaType.VIDEO
                and config["match"]["ignore_video_tracks"].get(bool)
                or not release.tracks
            ):
                ignored_discs.add(disc_number)
                continue
            disc.total = max(
                {
                    track.track_number
                    for track in release.tracks
                    if track.disc_number == disc_number
                }
            )

        va: bool = release.disc_type == DiscTypes.COMPILATION
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

        artists, artists_ids, artist_id = self.extract_artists_from_categories(
            artist_categories
        )

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
        for weblink in release.web_links:
            if not weblink.disabled and match(
                "Amazon( \\((LE|RE|JP|US)\\).*)?$", weblink.description
            ):
                asin_match: Match[str] | None = search(
                    "\\/dp\\/(.+?)(\\/|$)", weblink.url
                )
                if asin_match:
                    asin = asin_match[1]
                    break
        albumtype: str | None = release.disc_type.value
        albumtypes: list[str] | None = None
        if albumtype:
            albumtype = albumtype.lower()
            albumtypes = [albumtype]
        date: ReleaseDate | None = release.release_date
        year: int | None
        month: int | None
        day: int | None
        if date and not date.is_empty:
            year = date.year
            month = date.month
            day = date.day
        else:
            year = month = day = None
        label: str | None = None
        albumartist: AlbumArtist
        for albumartist in release.artists:
            if ArtistCategories.LABEL in albumartist.categories:
                label = albumartist.name
                break
        discs: Sequence[Disc] = release.discs
        mediums: int = len(discs)
        catalognum: str | None = release.catalog_number
        genre: str | None = self.get_genres(release.tags)
        media: str | None
        try:
            media = discs[0].name
        except IndexError:
            media = None
        data_url: str = urljoin(self.base_url, f"Al/{album_id}")
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

        artists, artists_ids, artist_id = self.extract_artists_from_categories(
            artist_categories
        )

        arranger: str = ", ".join(artist_categories.arrangers)
        composer: str = ", ".join(artist_categories.composers)
        lyricist: str = ", ".join(artist_categories.lyricists)
        length: float = recording.length_seconds
        data_url: str = urljoin(self.base_url, f"S/{track_id}")
        max_milli_bpm: int | None = recording.max_milli_bpm
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
        if recording.publish_date:
            date: datetime = recording.publish_date
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
            disc_number: int = track.disc_number
            if disc_number in ignored_discs or not track.song:
                continue
            format: str = discs[disc_number - 1].name
            total: int | None = discs[disc_number - 1].total
            track_info: TrackInfo = self.track_info(
                recording=track.song,
                index=index + 1,
                media=format,
                medium=disc_number,
                medium_index=track.track_number,
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

        artists_by_categories, support_artists = self.get_artists_by_categories(
            artists
        )
        va_name: str = config["va_name"].as_str()

        main_artists: list[str] = (
            [va_name]
            if comp
            else [
                name
                for name in (
                    *artists_by_categories.producers.keys(),
                    *artists_by_categories.circles.keys(),
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
            if (
                featured_artists
                and not len(main_artists) + len(featured_artists) > 5
            ):
                artist_string += " feat. " + ", ".join(featured_artists)

        return artists_by_categories, artist_string

    @staticmethod
    def get_artists_by_categories(
        artists: SongOrAlbumArtists,
    ) -> tuple[ArtistsByCategories, set[str]]:
        """Categorizes artists by their roles and identifies support artists.

        Takes a list of artists and organizes them into categories like producers,
        circles, vocalists, etc. based on their roles and categories. Also identifies
        which artists are marked as support artists.

        Args:
            artists: List of either AlbumArtist or SongArtist objects to categorize

        Returns:
            Tuple containing:
            - ArtistsByCategories object with artists sorted into role categories
            - Set of artist names that are marked as support artists
        """
        artists_by_categories: ArtistsByCategories = ArtistsByCategories()
        support_artists: set[str] = set()

        role_category_map = {
            ArtistCategories.CIRCLE: artists_by_categories.circles,
            ArtistRoles.ARRANGER: artists_by_categories.arrangers,
            ArtistRoles.COMPOSER: artists_by_categories.composers,
            ArtistRoles.LYRICIST: artists_by_categories.lyricists,
            ArtistCategories.VOCALIST: artists_by_categories.vocalists,
        }

        producer_roles = {
            ArtistRoles.ARRANGER,
            ArtistRoles.COMPOSER,
            ArtistRoles.LYRICIST,
        }

        artist: AlbumArtist | SongArtist
        for artist in artists:
            name, id = (
                (artist.artist.name, str(artist.artist.id))
                if artist.artist
                else (artist.name, "")
            )

            if artist.is_support:
                support_artists.add(name)

            # Handle producers/bands first
            if {
                ArtistCategories.PRODUCER,
                ArtistCategories.BAND,
            } & artist.categories:
                if ArtistRoles.DEFAULT in artist.effective_roles:
                    artist.effective_roles |= producer_roles
                artists_by_categories.producers[name] = id

            # Apply role/category mappings
            for role, category in role_category_map.items():
                if (
                    isinstance(role, ArtistCategories)
                    and role in artist.categories
                ):
                    category[name] = id
                elif role in artist.effective_roles:
                    category[name] = id

        # Set producer fallbacks if needed
        if (
            not artists_by_categories.producers
            and artists_by_categories.vocalists
        ):
            artists_by_categories.producers = artists_by_categories.vocalists

        # Set other role fallbacks
        for category in (
            artists_by_categories.arrangers,
            artists_by_categories.composers,
            artists_by_categories.lyricists,
        ):
            if not category:
                category |= artists_by_categories.producers

        return artists_by_categories, support_artists

    def extract_artists_from_categories(
        self, artist_categories: ArtistsByCategories
    ) -> tuple[list[str], list[str], str | None]:
        """
        Extracts relevant artists and their IDs.

        Args:
            artist_categories: ArtistsByCategories object containing categorized artists

        Returns:
            Tuple containing:
            - List of unique artist names in order of first appearance
            - List of corresponding artist IDs in same order as artist names
            - First artist ID from the list or None if no artists exist
        """

        category: dict[str, str]
        artists_dict: dict[str, str] = {}

        for category in msgspec.structs.astuple(artist_categories):
            # Merge each category's artists into the dict while preserving order
            # and preventing duplicates
            artists_dict |= category

        # Convert dict to separate lists of artists and IDs
        artists: list[str] = list(artists_dict.keys())
        artists_ids: list[str] = list(artists_dict.values())

        artist_id: str | None
        try:
            artist_id = artists_ids[0]
        except IndexError:
            artist_id = None

        return artists, artists_ids, artist_id

    @staticmethod
    def get_genres(tags: list[TagUsage]) -> str | None:
        genres: list[str] = []
        tag_usage: TagUsage
        for tag_usage in sorted(tags, reverse=True, key=lambda x: x.count):
            tag: Tag = tag_usage.tag
            if not tag.category_name == "Genres":
                continue
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
            translation_type: TranslationType = lyric.translation_type
            value: str = lyric.value
            # get the intersection
            culture_codes: set[str] = lyric.culture_codes & {"en", "ja"}

            if not culture_codes:
                if (
                    not translated_lyrics
                    and language == "Romaji"
                    and translation_type == TranslationType.ROMANIZED
                ):
                    out_lyrics = value
                continue

            if "en" in culture_codes:
                if translation_type == TranslationType.ORIGINAL:
                    out_script = "Latn"
                    out_language = "eng"
                if translated_lyrics or language == "English":
                    out_lyrics = value
                continue

            if "ja" in culture_codes:
                if translation_type == TranslationType.ORIGINAL:
                    out_script = "Jpan"
                    out_language = "jpn"
                if not translated_lyrics and language == "Japanese":
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
                if "en" in lyric.culture_codes:
                    return lyric.value
            language = "Romaji"
        if language == "Romaji":
            for lyric in lyrics:
                if lyric.translation_type == TranslationType.ROMANIZED:
                    return lyric.value
        return lyrics[0].value if lyrics else None
