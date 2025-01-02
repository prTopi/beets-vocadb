from collections.abc import Iterable, Sequence
from datetime import datetime
from itertools import chain
from json import load
from optparse import Values
from re import Match, match, search
from typing import NamedTuple, Optional, TypedDict, TYPE_CHECKING, Union
from sys import version_info

from confuse import AttrDict

if version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired
if version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from _typeshed import SupportsRead

import beets
from beets import autotag, config, library, ui, util
from beets.autotag.hooks import AlbumInfo, TrackInfo, Distance
from beets.autotag.match import track_distance
from beets.library import Album, Item, Library
from beets.plugins import BeetsPlugin, apply_item_changes, get_distance
from beets.ui import show_model_changes, Subcommand


USER_AGENT: str = f"beets/{beets.__version__} +https://beets.io/"
HEADERS: dict[str, str] = {"accept": "application/json", "User-Agent": USER_AGENT}

class InstanceInfo(NamedTuple):
    """Information about a specific instance of VocaDB"""

    name: str
    base_url: str
    api_url: str
    subcommand: str


class ConfigDict(AttrDict):
    """Stores configuration options conveniently"""

    def __init__(
        self,
        prefer_romaji: bool,
        translated_lyrics: bool,
        include_featured_album_artists: bool,
        va_name: str,
        max_results: int,
    ):
        super().__init__()
        self.prefer_romaji: bool = prefer_romaji
        self.translated_lyrics: bool = translated_lyrics
        self.include_featured_album_artists: bool = include_featured_album_artists
        self.va_name: str = va_name
        self.max_results: int = max_results


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


class ArtistsByCategoriesDict(TypedDict):
    producers: dict[str, str]
    circles: dict[str, str]
    vocalists: dict[str, str]
    arrangers: dict[str, str]
    composers: dict[str, str]
    lyricists: dict[str, str]


class VocaDBPlugin(BeetsPlugin):

    default_config: ConfigDict = ConfigDict(
        prefer_romaji=False,
        translated_lyrics=False,
        include_featured_album_artists=False,
        va_name="Various artists",
        max_results=5
    )

    user_agent: str = USER_AGENT
    headers: dict[str, str] = HEADERS
    languages: Optional[Iterable[str]] = config["import"]["languages"].as_str_seq()
    song_fields: str = "Artists,Tags,Bpm,Lyrics"

    instance_info: InstanceInfo = InstanceInfo(
        name="VocaDB",
        base_url="https://vocadb.net/",
        api_url="https://vocadb.net/api/",
        subcommand="vdbsync",
    )

    def __init__(self) -> None:
        super().__init__()
        self.data_source: str = self.instance_info.name
        self.config.add({
                "source_weight": 0.5,
            })
        self.config.add(self.default_config)
        self.instance_config: ConfigDict = ConfigDict(
            prefer_romaji=self.config["prefer_romaji"].get(bool),
            translated_lyrics=self.config["translated_lyrics"].get(bool),
            include_featured_album_artists=self.config["include_featured_album_artists"].get(bool),
            va_name=self.config["va_name"].as_str(),
            max_results=self.config["max_results"].get(int)
        )
        self.language: str = self._language

    def __init_subclass__(cls, instance_info: InstanceInfo) -> None:
        super().__init_subclass__()
        cls.instance_info = instance_info
        for key in set(cls.default_config.keys()).intersection(config["vocadb"].keys()):
            cls.default_config[key] = config["vocadb"][key].get()

    @property
    def _language(self) -> str:
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
    def commands(self) -> tuple[Subcommand, ...]:
        cmd: Subcommand = Subcommand(
            self.instance_info.subcommand,
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
            track_id: Optional[str] = item.get("mb_trackid")
            if not track_id:
                self._log.debug(
                    "Skipping singleton with no mb_trackid: {0}",
                    item_formatted,
                )
                continue
            if not (item.data_source == self.data_source and track_id.isnumeric()):
                self._log.debug(
                    "Skipping non-{0} singleton: {1}",
                    self.data_source,
                    item_formatted,
                )
                continue
            track_info: Optional[TrackInfo] = self.track_for_id(track_id)
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
        album: Album
        for album in lib.albums(query):
            album_formatted: str = format(album)
            if not album.mb_albumid:
                self._log.debug(
                    "Skipping album with no mb_albumid: {0}",
                    album_formatted,
                )
                continue
            if not (
                album.get("data_source") == self.data_source
                and album.mb_albumid.isnumeric()
            ):
                self._log.debug(
                    "Skipping non-{0} album: {1}",
                    self.data_source,
                    album_formatted,
                )
                continue
            album_info: Optional[AlbumInfo] = self.album_for_id(album.mb_albumid)
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

            self._log.debug("applying changes to {}", album_formatted)
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
        extra_tags: Optional[dict[str, object]] = None,
    ) -> Union[tuple[()], tuple[AlbumInfo, ...]]:
        self._log.debug("Searching for album {0}", album)
        url: str = urljoin(
            self.instance_info.api_url,
            f"albums/?query={quote(album)}&maxResults={self.instance_config.max_results}&nameMatchMode=Auto",
        )
        request: Request = Request(url, headers=self.headers)
        result: SupportsRead[Union[str, bytes]]
        try:
            with urlopen(request) as result:
                if result:
                    result_dict: AlbumFindResultDict = load(result)
                    albums: list[AlbumDict] = result_dict.get("items", [])
                    self._log.debug(
                        "Found {0} result(s) for '{1}'",
                        len(albums),
                        album,
                    )
                    # songFields parameter doesn't exist for album search
                    # so we'll get albums by their id
                    ids: set[str] = {str(album.get("id")) for album in albums}
                    return tuple(map(self.album_for_id, ids))
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return ()
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return ()

    @override
    def item_candidates(
        self, item: Item, artist: str, title: str
    ) -> tuple[TrackInfo, ...]:
        self._log.debug("Searching for track {0}", item)
        url: str = urljoin(
            self.instance_info.api_url,
            f"songs/?query={quote(title)}"
            + f"&fields={self.song_fields}"
            + f"&lang={self.language}"
            + f"&maxResults={self.instance_config.max_results}"
            + "&sort=SongType&preferAccurateMatches=true&nameMatchMode=Auto",
        )
        request: Request = Request(url, headers=self.headers)
        result: SupportsRead[Union[str, bytes]]
        try:
            with urlopen(request) as result:
                if result:
                    result_dict: SongFindResultDict = load(result)
                    items: list[SongDict] = result_dict.get("items", [])
                    self._log.debug(
                        "Found {0} result(s) for '{1}'",
                        len(items),
                        title,
                    )
                    return tuple(filter(None, map(self.track_info, items)))
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return ()
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return ()

    @override
    def album_for_id(self, album_id: str) -> Optional[AlbumInfo]:
        if not album_id.isnumeric():
            self._log.debug(
                "Skipping non-{0} album: {1}",
                self.data_source,
                album_id,
            )
            return None
        self._log.debug("Searching for album {0}", album_id)
        language: str = self.language
        url: str = urljoin(
            self.instance_info.api_url,
            f"albums/{album_id}"
            + "?fields=Artists,Discs,Tags,Tracks,WebLinks"
            + f"&songFields={self.song_fields}"
            + f"&lang={language}",
        )
        request: Request = Request(url, headers=self.headers)
        result: SupportsRead[Union[str, bytes]]
        try:
            with urlopen(request) as result:
                if result:
                    result_dict: AlbumDict = load(result)
                    return self.album_info(result_dict, search_lang=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return None
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return None

    @override
    def track_for_id(self, track_id: str) -> Optional[TrackInfo]:
        if not track_id.isnumeric():
            self._log.debug(
                "Skipping non-{0} singleton: {1}",
                self.data_source,
                track_id,
            )
            return None
        self._log.debug("Searching for track {0}", track_id)
        language: str = self.language
        url: str = urljoin(
            self.instance_info.api_url,
            f"songs/{track_id}" + f"?fields={self.song_fields}" + f"&lang={language}",
        )
        request: Request = Request(url, headers=self.headers)
        result: SupportsRead[Union[str, bytes]]
        try:
            with urlopen(request) as result:
                if result:
                    result_dict: SongDict = load(result)
                    return self.track_info(result_dict, search_lang=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return None
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return None

    def album_info(
        self, release: AlbumDict, search_lang: Optional[str] = None
    ) -> AlbumInfo:
        if not release.get("discs"):
            release["discs"] = [
                DiscDict(discNumber=i + 1, name="CD", mediaType="Audio")
                for i in range(
                    max(
                        track.get("discNumber", 0)
                        for track in release.get("tracks", [])
                    )
                )
            ]
        ignored_discs: set[int] = set()
        disc: DiscDict
        for disc in release.get("discs", []):
            disc_number: Optional[int] = disc.get("discNumber")
            if (
                disc.get("mediaType") == "Video"
                and config["match"]["ignore_video_tracks"].get(bool)
                or not release.get("tracks")
            ):
                if disc_number is not None:
                    ignored_discs.add(disc_number)
            else:
                disc["total"] = max(
                    [
                        track.get("trackNumber", 0)
                        for track in release.get("tracks", [])
                        if track.get("discNumber") == disc_number
                    ]
                )

        va: bool = release.get("discType") == "Compilation"
        album: Optional[str] = release.get("name")
        album_id: Optional[str] = str(release.get("id"))
        artist_categories: ArtistsByCategoriesDict
        artist: str
        artist_categories, artist = self.get_artists(
            release.get("artists", []),
            include_featured_artists=self.instance_config.include_featured_album_artists,
            comp=va,
        )
        if artist == self.instance_config.va_name:
            va = True
        # for membership checks in constant time
        artists_set: set[str] = set()
        artists_ids_set: set[str] = set()
        artists: list[str] = []
        artists_ids: list[str] = []
        category: dict[str, str]
        for category in artist_categories.values():
            keys: list[str] = list(category.keys())
            values: list[str] = list(category.values())
            artists_set.update(keys)
            artists_ids_set.update(values)
            artists.extend(filter(lambda artist: artist not in artists_set, keys))
            artists_ids.extend(
                filter(lambda artist_id: artist_id not in artists_ids_set, values)
            )
        artist_id: Optional[str]
        try:
            artist_id = artists_ids[0]
        except IndexError:
            artist_id = None
        tracks: list[TrackInfo]
        script: Optional[str]
        language: Optional[str]
        tracks, script, language = self.get_album_track_infos(
            release.get("tracks", []),
            release.get("discs", []),
            ignored_discs,
            search_lang,
        )
        weblink: WebLinkDict
        asin_match: Optional[Match[str]] = None
        asin: Optional[str] = None
        for weblink in release.get("webLinks", []):
            if not weblink.get("disabled") and match(
                "Amazon( \\((LE|RE|JP|US)\\).*)?$", weblink.get("description", "")
            ):
                asin_match = search("\\/dp\\/(.+?)(\\/|$)", weblink.get("url", ""))
                if asin_match:
                    asin = asin_match[1]
                    break
        albumtype: Optional[str] = release.get("discType")
        albumtypes: Optional[list[str]] = None
        if albumtype:
            albumtype = albumtype.lower()
            albumtypes = [albumtype]
        date: Optional[ReleaseDateDict] = release.get("releaseDate")
        year: Optional[int]
        month: Optional[int]
        day: Optional[int]
        if date and not date.get("isEmpty", True):
            year = date.get("year")
            month = date.get("month")
            day = date.get("day")
        else:
            year = month = day = None
        label: Optional[str] = None
        albumartist: AlbumOrSongArtistDict
        for albumartist in release.get("artists", []):
            if "Label" in albumartist.get("categories", ""):
                label = albumartist.get("name")
                break
        discs: Sequence[DiscDict] = release.get("discs", [])
        mediums: int = len(discs)
        catalognum: Optional[str] = release.get("catalogNumber")
        genre: Optional[str] = self.get_genres(release.get("tags", []))
        media: Optional[str]
        try:
            media = discs[0].get("name")
        except IndexError:
            media = None
        data_url: str = urljoin(self.instance_info.base_url, f"Al/{album_id}")
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
        recording: SongDict,
        index: Optional[int] = None,
        media: Optional[str] = None,
        medium: Optional[int] = None,
        medium_index: Optional[int] = None,
        medium_total: Optional[int] = None,
        search_lang: Optional[str] = None,
    ) -> TrackInfo:
        title: str = str(recording.get("name", ""))
        track_id: str = str(recording.get("id", ""))
        artist_categories: ArtistsByCategoriesDict
        artist: str
        artist_categories, artist = self.get_artists(recording.get("artists", []))
        # for membership checks in constant time
        artists_set: set[str] = set()
        artists_ids_set: set[str] = set()
        artists: list[str] = []
        artists_ids: list[str] = []
        category: dict[str, str]
        for category in artist_categories.values():
            keys: list[str] = list(category.keys())
            values: list[str] = list(category.values())
            artists_set.update(keys)
            artists_ids_set.update(values)
            artists.extend(filter(lambda artist: artist not in artists_set, keys))
            artists_ids.extend(
                filter(lambda artist_id: artist_id not in artists_ids_set, values)
            )
        artist_id: Optional[str]
        try:
            artist_id = artists_ids[0]
        except IndexError:
            artist_id = None
        arranger: str = ", ".join(artist_categories["arrangers"])
        composer: str = ", ".join(artist_categories["composers"])
        lyricist: str = ", ".join(artist_categories["lyricists"])
        length: float = recording.get("lengthSeconds", 0)
        data_url: str = urljoin(self.instance_info.base_url, f"S/{track_id}")
        max_milli_bpm: Optional[int] = recording.get("maxMilliBpm")
        bpm: Optional[str] = str(max_milli_bpm // 1000) if max_milli_bpm else None
        genre: Optional[str] = self.get_genres(recording.get("tags", []))
        script: Optional[str]
        language: Optional[str]
        lyrics: Optional[str]
        script, language, lyrics = self.get_lyrics(
            recording.get("lyrics", []),
            search_lang,
        )
        original_day: Optional[int] = None
        original_month: Optional[int] = None
        original_year: Optional[int] = None
        if "publishDate" in recording:
            date: datetime = datetime.fromisoformat(
                recording.get("publishDate", "")[:-1]
            )
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
        tracks: list[SongInAlbumDict],
        discs: Sequence[DiscDict],
        ignored_discs: set[int],
        search_lang: Optional[str],
    ) -> tuple[list[TrackInfo], Optional[str], Optional[str]]:
        track_infos: list[TrackInfo] = []
        script: Optional[str] = None
        language: Optional[str] = None
        index: int
        track: SongInAlbumDict
        for index, track in enumerate(tracks):
            disc_number: Optional[int] = track.get("discNumber")
            if disc_number in ignored_discs or "song" not in track:
                continue
            if disc_number is not None:
                format: Optional[str] = discs[disc_number - 1].get("name")
                total: Optional[int] = discs[disc_number - 1].get("total")
            track_info: TrackInfo = self.track_info(
                recording=track["song"],
                index=index + 1,
                media=format,
                medium=disc_number,
                medium_index=track.get("trackNumber"),
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
        artists: list[AlbumOrSongArtistDict],
        include_featured_artists: bool = True,
        comp: bool = False,
    ) -> tuple[ArtistsByCategoriesDict, str]:
        va_name: str = self.instance_config.va_name
        artists_by_categories: ArtistsByCategoriesDict
        is_support: dict[str, bool]
        artists_by_categories, is_support = self.get_artists_by_categories(artists)

        artist_string: Optional[str] = None
        main_artists: Optional[list[str]] = None

        if not comp:
            main_artists = [
                name
                for name, id in chain(
                    artists_by_categories["producers"].items(),
                    artists_by_categories["circles"].items(),
                )
                if not is_support.get(id)
            ]
            if not len(main_artists) > 5:
                artist_string = ", ".join(main_artists)

        if not artist_string:
            artist_string = va_name

        if (
            include_featured_artists
            and artists_by_categories["vocalists"]
            and main_artists
        ):
            featured_artists: list[str] = [
                name
                for name, id in artists_by_categories["vocalists"].items()
                if not is_support.get(id)
            ]
            if featured_artists and not len(main_artists) + len(featured_artists) > 5:
                artist_string += " feat. " + ", ".join(featured_artists)

        return artists_by_categories, artist_string

    @staticmethod
    def get_artists_by_categories(
        artists: list[AlbumOrSongArtistDict],
    ) -> tuple[ArtistsByCategoriesDict, dict[str, bool]]:
        artists_by_categories: ArtistsByCategoriesDict = ArtistsByCategoriesDict(
            producers={},
            circles={},
            vocalists={},
            arrangers={},
            composers={},
            lyricists={}
        )
        is_support: dict[str, bool] = {}
        artist: AlbumOrSongArtistDict
        for artist in filter(None, artists):
            parent: Optional[ArtistDict] = artist.get("artist")
            name: str
            id: str
            if parent:
                name = parent.get("name", "")
                id = str(parent.get("id", ""))
            else:
                name = artist.get("name", "")
                id = ""
            is_support[id] = artist.get("isSupport", False)
            categories: str = artist.get("categories", "")
            effectiveRoles: str = artist.get("effectiveRoles", "")
            if "Producer" in categories or "Band" in categories:
                if "Default" in artist["effectiveRoles"]:
                    artist["effectiveRoles"] += ",Arranger,Composer,Lyricist"
                    effectiveRoles = artist["effectiveRoles"]
                artists_by_categories["producers"][name] = id
            if "Circle" in categories:
                artists_by_categories["circles"][name] = id
            if "Arranger" in effectiveRoles:
                artists_by_categories["arrangers"][name] = id
            if "Composer" in effectiveRoles:
                artists_by_categories["composers"][name] = id
            if "Lyricist" in effectiveRoles:
                artists_by_categories["lyricists"][name] = id
            if "Vocalist" in categories:
                artists_by_categories["vocalists"][name] = id
        if (
            not artists_by_categories["producers"]
            and artists_by_categories["vocalists"]
        ):
            artists_by_categories["producers"] = artists_by_categories["vocalists"]
        if not artists_by_categories["arrangers"]:
            artists_by_categories["arrangers"] = artists_by_categories["producers"]
        if not artists_by_categories["composers"]:
            artists_by_categories["composers"] = artists_by_categories["producers"]
        if not artists_by_categories["lyricists"]:
            artists_by_categories["lyricists"] = artists_by_categories["producers"]
        return artists_by_categories, is_support

    @staticmethod
    def get_genres(tags: list[TagUsageDict]) -> Optional[str]:
        genres: list[str] = []
        tag_usage: TagUsageDict
        for tag_usage in sorted(tags, reverse=True, key=lambda x: x.get("count", 0)):
            tag: TagDict = tag_usage.get("tag", {})
            if tag.get("categoryName") == "Genres":
                tag_name: Optional[str] = tag.get("name")
                if tag_name:
                    genres.append(tag_name.title())
        return "; ".join(genres) if len(genres) > 0 else None

    @classmethod
    def get_lyrics(
        cls,
        lyrics: list[LyricsDict],
        language: Optional[str] = None,
        translated_lyrics: bool = False,
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        out_script: Optional[str] = None
        out_language: Optional[str] = None
        out_lyrics: Optional[str] = None
        lyric: LyricsDict
        culture_codes: set[str]
        for lyric in lyrics:
            culture_codes = set(lyric.get("cultureCodes"))
            translation_type: Optional[str] = lyric.get("translationType")
            value: Optional[str] = lyric.get("value")
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
        lyrics: list[LyricsDict], language: Optional[str]
    ) -> Optional[str]:
        lyric: LyricsDict
        if language == "English":
            for lyric in lyrics:
                if "en" in lyric.get("cultureCodes", ""):
                    return lyric.get("value")
            language = "Romaji"
        if language == "Romaji":
            for lyric in lyrics:
                if lyric.get("translationType") == "Romanized":
                    return lyric.get("value")
        return lyrics[0].get("value")
