from collections.abc import Sequence
from datetime import datetime
from itertools import chain
from json import load
from optparse import Values
from re import Match, match, search
from typing import NamedTuple, Optional, TypedDict, TYPE_CHECKING, Union
from sys import version_info

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


class InstanceInfo(NamedTuple):
    """Information about a specific instance of VocaDB"""

    name: str
    base_url: str
    api_url: str
    subcommand: str


class APIResultDict(TypedDict):
    id: NotRequired[int]


class ArtistDict(APIResultDict):
    additionalNames: str
    artistType: str
    deleted: bool
    name: NotRequired[str]
    pictureMime: str
    status: str
    version: int


class AlbumArtistDict(APIResultDict):
    artist: NotRequired[ArtistDict]
    categories: str
    effectiveRoles: str
    isSupport: bool
    name: NotRequired[str]
    roles: str


class TagDict(APIResultDict):
    additionalNames: NotRequired[str]
    categoryName: NotRequired[str]
    name: str
    urlSlug: NotRequired[str]


class TagUsageDict(TypedDict):
    count: int
    tag: TagDict


class InfoDict(APIResultDict):
    artists: NotRequired[list[AlbumArtistDict]]
    artistString: NotRequired[str]
    createDate: NotRequired[str]
    defaultName: NotRequired[str]
    defaultNameLanguage: NotRequired[str]
    name: NotRequired[str]
    status: NotRequired[str]
    tags: NotRequired[list[TagUsageDict]]


class LyricsDict(APIResultDict):
    cultureCodes: list[str]
    source: NotRequired[str]
    translationType: str
    url: NotRequired[str]
    value: str


class DiscDict(APIResultDict):
    discNumber: int
    mediaType: str
    name: NotRequired[str]
    total: NotRequired[int]


class ReleaseDateDict(TypedDict):
    day: NotRequired[int]
    isEmpty: NotRequired[bool]
    month: NotRequired[int]
    year: NotRequired[int]


class SongDict(InfoDict):
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


class SongInAlbumDict(APIResultDict):
    discNumber: int
    name: NotRequired[str]
    song: SongDict
    trackNumber: int
    computedCultureCodes: list[str]


class WebLinkDict(APIResultDict):
    category: str
    description: str
    descriptionOrUrl: str
    disabled: bool
    url: str


class AlbumDict(InfoDict):
    catalogNumber: NotRequired[str]
    discs: Sequence[NotRequired[DiscDict]]
    discType: NotRequired[str]
    releaseDate: NotRequired[ReleaseDateDict]
    tracks: list[SongInAlbumDict]
    webLinks: NotRequired[list[WebLinkDict]]


class FindResultDict(APIResultDict):
    term: str
    totalCount: int


class SongFindResultDict(FindResultDict):
    items: list[SongDict]


class AlbumFindResultDict(FindResultDict):
    items: list[AlbumDict]


class ConfigDict(TypedDict):
    prefer_romaji: bool
    translated_lyrics: bool
    include_featured_album_artists: bool
    va_string: str
    max_results: int


class VocaDBPlugin(BeetsPlugin):

    default_config: ConfigDict = {
        "prefer_romaji": False,
        "translated_lyrics": False,
        "include_featured_album_artists": False,
        "va_string": "Various artists",
        "max_results": 5,
    }

    user_agent: str = f"beets/{beets.__version__} +https://beets.io/"
    headers: dict[str, str] = {"accept": "application/json", "User-Agent": user_agent}
    languages: Optional[Sequence[str]] = config["import"]["languages"].as_str_seq()
    song_fields: str = "Artists,Tags,Bpm,Lyrics"

    instance_info: InstanceInfo = InstanceInfo(
        name="VocaDB",
        base_url="https://vocadb.net/",
        api_url="https://vocadb.net/api/",
        subcommand="vdbsync",
    )

    def __init__(self) -> None:
        super().__init__()
        self.config.add(
            {
                "source_weight": 0.5,
            }
        )
        self.config.add(self.default_config)

        self.data_source: str = self.instance_info.name

    def __init_subclass__(cls, instance_info: InstanceInfo) -> None:
        super().__init_subclass__()
        cls.instance_info = instance_info
        vocadb_config = config["vocadb"]
        if vocadb_config.exists():
            for key in vocadb_config.keys():
                cls.default_config[key] = vocadb_config[key].get()

    @property
    def language(self) -> str:
        if not self.languages:
            return "English"

        lang: str
        for lang in self.languages:
            if lang == "jp":
                return "Romaji" if self.prefer_romaji else "Japanese"
            if lang == "en":
                return "English"

        return "English"  # Default if no matching language found

    @property
    def prefer_romaji(self) -> bool:
        return bool(self.config["prefer_romaji"].get())

    @property
    def translated_lyrics(self) -> bool:
        return bool(self.config["translated_lyrics"].get())

    @property
    def include_featured_album_artists(self) -> bool:
        return bool(self.config["include_featured_album_artists"].get())

    @property
    def va_string(self) -> str:
        return self.config["va_string"].as_str()

    @property
    def max_results(self) -> str:
        return self.config["max_results"].as_str()

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
            if not item.mb_trackid:
                self._log.debug(
                    "Skipping singleton with no mb_trackid: {0}",
                    item_formatted,
                )
                continue
            if not (
                item.get("data_source") == self.data_source
                and item.mb_trackid.isnumeric()
            ):
                self._log.debug(
                    "Skipping non-{0} singleton: {1}",
                    self.data_source,
                    item_formatted,
                )
                continue
            track_info: Optional[TrackInfo] = self.track_for_id(item.mb_trackid)
            if not (track_info):
                self._log.info(
                    "Recording ID not found: {0} for track {1}",
                    item.mb_trackid,
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
            items: Sequence[Item] = list(album.items())
            item: Item
            track_index: dict[str, TrackInfo] = {
                str(track.track_id): track for track in album_info.tracks
            }
            mapping: dict[Item, TrackInfo] = {}
            for item in items:
                if item.mb_trackid not in track_index:
                    old_track_id: str = item.mb_trackid
                    # Unset track id so that it won't affect distance
                    item.mb_trackid = None
                    matches: dict[str, Distance] = {
                        track_info["track_id"]: track_distance(item, track_info)
                        for track_info in track_index.values()
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
                        if key not in [
                            "original_day",
                            "original_month",
                            "original_year",
                            "genre",
                        ]:
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
        items: Sequence[Item],
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
        items: Sequence[Item],
        artist: str,
        album: str,
        va_likely: bool,
        extra_tags: Optional[dict] = None,
    ) -> tuple[AlbumInfo, ...]:
        self._log.debug("Searching for album {0}", album)
        url: str = urljoin(
            self.instance_info.api_url,
            f"albums/?query={quote(album)}&maxResults={self.max_results}&nameMatchMode=Auto",
        )
        request: Request = Request(url, headers=self.headers)
        result: SupportsRead[Union[str, bytes]]
        try:
            with urlopen(request) as result:
                if result:
                    result_dict: AlbumFindResultDict = load(result)
                    self._log.debug(
                        "Found {0} result(s) for '{1}'",
                        len(result_dict["items"]),
                        album,
                    )
                    # songFields parameter doesn't exist for album search
                    # so we'll get albums by their id
                    ids: list[str] = [
                        str(item.get("id")) for item in result_dict["items"]
                    ]
                    return tuple(
                        [album for album in map(self.album_for_id, ids) if album]
                    )
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
            + f"&maxResults={self.max_results}"
            + "&sort=SongType&preferAccurateMatches=true&nameMatchMode=Auto",
        )
        request: Request = Request(url, headers=self.headers)
        result: SupportsRead[Union[str, bytes]]
        try:
            with urlopen(request) as result:
                if result:
                    result_dict: SongFindResultDict = load(result)
                    self._log.debug(
                        "Found {0} result(s) for '{1}'",
                        len(result_dict["items"]),
                        title,
                    )
                    return tuple(
                        [
                            track
                            for track in map(self.track_info, result_dict["items"])
                            if track
                        ]
                    )
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
        discs: int = len(
            set([track["discNumber"] for track in release.get("tracks", [])])
        )
        if not release.get("discs"):
            release["discs"] = [
                {"discNumber": x + 1, "name": "CD", "mediaType": "Audio"}
                for x in range(discs)
            ]
        ignored_discs: list[int] = []
        disc: DiscDict
        for disc in release.get("discs", []):
            if (
                disc["mediaType"] == "Video"
                and config["match"]["ignore_video_tracks"]
                or not release.get("tracks")
            ):
                ignored_discs.append(disc["discNumber"])
            else:
                disc["total"] = max(
                    [
                        y
                        for y in release.get("tracks", {})
                        if y.get("discNumber") == disc["discNumber"]
                    ],
                    key=lambda y: y["trackNumber"],
                )["trackNumber"]

        va: bool = release.get("discType", "") == "Compilation"
        album: str = release.get("name", "")
        album_id: str = str(release.get("id", ""))
        artist_categories: dict[str, dict[str, str]]
        artist: str
        artist_categories, artist = self.get_artists(
            release.get("artists", []),
            self.va_string,
            include_featured_artists=self.include_featured_album_artists,
            comp=va,
        )
        if artist == self.va_string:
            va = True
        artists: list[str] = []
        artists_ids: list[str] = []
        category: dict[str, str]
        for category in artist_categories.values():
            artists.extend(
                [artist for artist in category.keys() if artist not in artists]
            )
            artists_ids.extend(
                [id for id in category.values() if id not in artists_ids]
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
            release["tracks"], release.get("discs"), ignored_discs, search_lang
        )
        weblink: WebLinkDict
        asin_match: Optional[Match[str]] = None
        asin: Optional[str] = None
        for weblink in release.get("webLinks", []):
            if not weblink["disabled"] and match(
                "Amazon( \\((LE|RE|JP|US)\\).*)?$", weblink.get("description")
            ):
                asin_match = search("\\/dp\\/(.+?)(\\/|$)", weblink.get("url"))
                if asin_match:
                    asin = asin_match[1]
                    break
        albumtype: str = release.get("discType", "").lower()
        albumtypes: Optional[list[str]] = [albumtype] if albumtype else None
        date: ReleaseDateDict = release.get("releaseDate", ReleaseDateDict())
        year: Optional[int] = date.get("year")
        month: Optional[int] = date.get("month")
        day: Optional[int] = date.get("day")
        label: Optional[str] = None
        albumartist: AlbumArtistDict
        for albumartist in release.get("artists", []):
            if "Label" in albumartist.get("categories", ""):
                label = albumartist.get("name")
                break
        mediums: int = len(release["discs"])
        catalognum: Optional[str] = release.get("catalogNumber")
        genre: Optional[str] = self.get_genres(release)
        media: Optional[str]
        try:
            media = release["discs"][0].get("name")
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
        artist_categories: dict[str, dict[str, str]]
        artist: str
        artist_categories, artist = self.get_artists(
            recording.get("artists", []), self.va_string
        )
        category: dict[str, str]
        artists: list[str] = []
        artists_ids: list[str] = []
        for category in artist_categories.values():
            artists.extend(
                [artist for artist in category.keys() if artist not in artists]
            )
            artists_ids.extend(
                [id for id in category.values() if id not in artists_ids]
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
        genre: Optional[str] = self.get_genres(recording)
        script: Optional[str]
        language: Optional[str]
        lyrics: Optional[str]
        script, language, lyrics = self.get_lyrics(
            recording.get("lyrics", []), search_lang, self.translated_lyrics
        )
        original_day: Optional[int] = None
        original_month: Optional[int] = None
        original_year: Optional[int] = None
        if "publishDate" in recording:
            date: datetime = datetime.fromisoformat(recording["publishDate"][:-1])
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
        ignored_discs: list[int],
        search_lang: Optional[str],
    ) -> tuple[list[TrackInfo], Optional[str], Optional[str]]:
        track_infos: list[TrackInfo] = []
        script: Optional[str] = None
        language: Optional[str] = None
        index: int
        track: SongInAlbumDict
        for index, track in enumerate(tracks):
            if track["discNumber"] in ignored_discs or "song" not in track:
                continue
            format: Optional[str] = discs[track["discNumber"] - 1].get("name")
            total: Optional[int] = discs[track["discNumber"] - 1].get("total")
            track_info: TrackInfo = self.track_info(
                recording=track["song"],
                index=index + 1,
                media=format,
                medium=track.get("discNumber", None),
                medium_index=track.get("trackNumber", None),
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

    @classmethod
    def get_artists(
        cls,
        artists: list[AlbumArtistDict],
        va_string: str = default_config["va_string"],
        include_featured_artists: bool = True,
        comp: bool = False,
    ) -> tuple[dict[str, dict[str, str]], str]:
        artists_by_categories: dict[str, dict[str, str]]
        is_support: dict[str, bool]
        artists_by_categories, is_support = cls.get_artists_by_categories(artists)

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
            artist_string = va_string

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
        artists: list[AlbumArtistDict],
    ) -> tuple[dict[str, dict[str, str]], dict[str, bool]]:
        artists_by_categories: dict[str, dict[str, str]] = {
            key: {}
            for key in [
                "producers",
                "circles",
                "vocalists",
                "arrangers",
                "composers",
                "lyricists",
            ]
        }
        is_support: dict[str, bool] = {}
        artist: AlbumArtistDict
        for artist in artists:
            parent: Optional[ArtistDict] = artist.get("artist")
            name: str
            id: str
            if parent:
                name = parent.get("name", "")
                id = str(parent.get("id", ""))
            else:
                name = artist.get("name", "")
                id = ""
            is_support[id] = artist["isSupport"]
            categories: str = artist["categories"]
            effectiveRoles: str = artist["effectiveRoles"]
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
    def get_genres(info: InfoDict) -> Optional[str]:
        genres: list[str] = []
        tag_usage: TagUsageDict
        for tag_usage in sorted(
            info.get("tags", {}), reverse=True, key=lambda x: x.get("count")
        ):
            tag: TagDict = tag_usage.get("tag")
            if tag.get("categoryName") == "Genres":
                genres.append(tag.get("name").title())
        return "; ".join(genres) if len(genres) > 0 else None

    @classmethod
    def get_lyrics(
        cls,
        lyrics: list[LyricsDict],
        language: Optional[str],
        translated_lyrics: bool = False,
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        out_script: Optional[str] = None
        out_language: Optional[str] = None
        out_lyrics: Optional[str] = None
        lyric: LyricsDict
        for lyric in lyrics:
            if "en" in lyric["cultureCodes"]:
                if lyric["translationType"] == "Original":
                    out_script = "Latn"
                    out_language = "eng"
                if translated_lyrics or language == "English":
                    out_lyrics = lyric["value"]
            elif "ja" in lyric["cultureCodes"]:
                if lyric["translationType"] == "Original":
                    out_script = "Jpan"
                    out_language = "jpn"
                if not translated_lyrics and language == "Japanese":
                    out_lyrics = lyric["value"]
            if (
                not translated_lyrics
                and language == "Romaji"
                and lyric["translationType"] == "Romanized"
            ):
                out_lyrics = lyric["value"]
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
                if "en" in lyric["cultureCodes"]:
                    return lyric["value"]
            language = "Romaji"
        if language == "Romaji":
            for lyric in lyrics:
                if lyric["translationType"] == "Romanized":
                    return lyric["value"]
        return lyrics[0]["value"]
