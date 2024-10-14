from datetime import datetime
from itertools import chain
from json import load
from re import Match, match, search
from typing import Any, NamedTuple, Optional, Sequence
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

import beets
from beets import autotag, config, library, ui, util
from beets.autotag.hooks import AlbumInfo, TrackInfo, Distance
from beets.library import Item, Library
from beets.plugins import BeetsPlugin, apply_item_changes, get_distance
from beets.ui import show_model_changes, Subcommand

USER_AGENT = f"beets/{beets.__version__} +https://beets.io/"
HEADERS = {"accept": "application/json", "User-Agent": USER_AGENT}


class VocaDBInstance(NamedTuple):
    name: str
    base_url: str
    api_url: str
    subcommand: str


class VocaDBPlugin(BeetsPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.instance: VocaDBInstance = VocaDBInstance(
            name="VocaDB",
            base_url="https://vocadb.net/",
            api_url="https://vocadb.net/api/",
            subcommand="vdbsync",
        )
        self.data_source: str = self.instance.name
        self.config.add(
            {
                "source_weight": 0.5,
                "prefer_romaji": False,
                "translated_lyrics": False,
                "include_featured_album_artists": False,
                "va_string": "Various artists",
            }
        )
        self.va_string: str = str(self.config["va_string"].get())

    def commands(self) -> list[Subcommand]:
        cmd: Subcommand = Subcommand(
            self.instance.subcommand,
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
        return [cmd]

    def func(self, lib: Library, opts, args) -> None:
        """Command handler for the *dbsync function."""
        move: bool = ui.should_move(opts.move)
        pretend = opts.pretend
        write: bool = ui.should_write(opts.write)
        query = ui.decargs(args)

        self.singletons(lib, query, move, pretend, write)
        self.albums(lib, query, move, pretend, write)

    def singletons(self, lib: Library, query, move: bool, pretend, write: bool) -> None:
        """Retrieve and apply info from the autotagger for items matched by
        query.
        """
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
            track_info: Optional[TrackInfo]
            if not (track_info := self.track_for_id(item.mb_trackid)):
                self._log.info(
                    "Recording ID not found: {0} for track {0}",
                    item.mb_trackid,
                    item_formatted,
                )
                continue
            with lib.transaction():
                autotag.apply_item_metadata(item, track_info)
                show_model_changes(item)
                apply_item_changes(lib, item, move, pretend, write)

    def albums(self, lib: Library, query, move: bool, pretend, write: bool) -> None:
        """Retrieve and apply info from the autotagger for albums matched by
        query and their items.
        """
        for album in lib.albums(query):
            album_formatted: str = format(album)
            if not album.mb_albumid:
                self._log.debug(
                    "Skipping album with no mb_albumid: {0}",
                    album_formatted,
                )
                continue
            items: Sequence[Item] = list(album.items())
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
            album_info: Optional[AlbumInfo]
            if not (album_info := self.album_for_id(album.mb_albumid)):
                self._log.info(
                    "Release ID {0} not found for album {1}",
                    album.mb_albumid,
                    album_formatted,
                )
                continue
            trackid_to_trackinfo: dict[str, TrackInfo] = {
                str(track.track_id): track for track in album_info.tracks
            }
            library_trackid_to_item: dict[str, Item] = {
                str(item.mb_trackid): item for item in items
            }
            mapping: dict[Item, TrackInfo] = {}
            missing_tracks: list[str] = []
            for track_id, item in library_trackid_to_item.items():
                if track_id in trackid_to_trackinfo:
                    mapping[item] = trackid_to_trackinfo[track_id]
                else:
                    missing_tracks.append(track_id)
                    self._log.debug(
                        "Missing track ID {0} in album info for {1}",
                        track_id,
                        album_formatted,
                    )

            if missing_tracks:
                self._log.warning(
                    "The following track IDs were missing in the VocaDB album \
                    info for {0}: {1}",
                    album_formatted,
                    ", ".join(
                        str(track) for track in missing_tracks if track is not None
                    ),
                )

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

    def track_distance(self, item: Item, info: TrackInfo) -> Distance:
        """Returns the track distance."""
        return get_distance(data_source=self.data_source, info=info, config=self.config)

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

    def candidates(
        self,
        items: Sequence[Item],
        artist: str,
        album: str,
        va_likely: bool,
        extra_tags: Optional[dict] = None,
    ) -> list[AlbumInfo]:
        self._log.debug("Searching for album {0}", album)
        url: str = urljoin(
            self.instance.api_url,
            f"albums/?query={quote(album)}&maxResults=5&nameMatchMode=Auto",
        )
        request: Request = Request(url, headers=HEADERS)
        try:
            with urlopen(request) as result:
                if result:
                    result = load(result)
                    # songFields parameter doesn't exist for album search
                    # so we'll get albums by their id
                    ids: list[str] = [str(x["id"]) for x in result["items"]]
                    return [album for album in map(self.album_for_id, ids) if album]
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return []
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return []

    def item_candidates(self, item: Item, artist: str, title: str) -> list[TrackInfo]:
        self._log.debug("Searching for track {0}", item)
        language: str = self.get_lang(config["import"]["languages"].as_str_seq())
        url: str = urljoin(
            self.instance.api_url,
            f"songs/?query={quote(title)}"
            + f"&fields={self.get_song_fields()}"
            + f"&lang={language}"
            + "&maxResults=5&sort=SongType&preferAccurateMatches=true&nameMatchMode=Auto",
        )
        request: Request = Request(url, headers=HEADERS)
        try:
            with urlopen(request) as result:
                if result:
                    result = load(result)
                    return [
                        track
                        for track in map(self.track_info, result["items"])
                        if track
                    ]
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return []
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return []

    def album_for_id(self, album_id: str) -> Optional[AlbumInfo]:
        self._log.debug("Searching for album {0}", album_id)
        language: str = self.get_lang(config["import"]["languages"].as_str_seq())
        url: str = urljoin(
            self.instance.api_url,
            f"albums/{album_id}"
            + "?fields=Artists,Discs,Tags,Tracks,WebLinks"
            + f"&songFields={self.get_song_fields()}"
            + f"&lang={language}",
        )
        request = Request(url, headers=HEADERS)
        try:
            with urlopen(request) as result:
                if result:
                    result = load(result)
                    return self.album_info(result, search_lang=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return None
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return None

    def track_for_id(self, track_id: str) -> Optional[TrackInfo]:
        self._log.debug("Searching for track {0}", track_id)
        language: str = self.get_lang(config["import"]["languages"].as_str_seq())
        url: str = urljoin(
            self.instance.api_url,
            f"songs/{track_id}"
            + f"?fields={self.get_song_fields()}"
            + f"&lang={language}",
        )
        request: Request = Request(url, headers=HEADERS)
        try:
            with urlopen(request) as result:
                if result:
                    result = load(result)
                    return self.track_info(result, search_lang=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return None
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return None

    def album_info(
        self, release: dict[str, Any], search_lang: Optional[str] = None
    ) -> AlbumInfo:
        discs: int = len(set([x["discNumber"] for x in release["tracks"]]))
        if not release["discs"]:
            release["discs"] = [
                {"discNumber": x + 1, "name": "CD", "mediaType": "Audio"}
                for x in range(discs)
            ]
        ignored_discs: list[int] = []
        for x in release["discs"]:
            if (
                x["mediaType"] == "Video"
                and config["match"]["ignore_video_tracks"]
                or not release["tracks"]
            ):
                ignored_discs.append(x["discNumber"])
            else:
                x["total"] = max(
                    [
                        y
                        for y in release["tracks"]
                        if y["discNumber"] == x["discNumber"]
                    ],
                    key=lambda y: y["trackNumber"],
                )["trackNumber"]

        va: bool = release.get("discType", "") == "Compilation"
        include_featured_album_artists: bool = bool(self.config["include_featured_album_artists"].get())
        album: str = release["name"]
        album_id: str = str(release["id"])
        artist_categories, artist = self.get_artists(
            release["artists"], self.va_string, include_featured_artists=include_featured_album_artists, comp=va
        )
        if artist == self.va_string:
            va = True
        artists: list[str] = []
        artists_ids: list[str] = []
        for category in artist_categories.values():
            artists.extend(
                [artist for artist in category.keys() if artist not in artists]
            )
            artists_ids.extend(
                [id for id in category.values() if id not in artists_ids]
            )
        artist_id: Optional[str] = None
        try:
            artist_id = artists_ids[0]
        except IndexError:
            pass
        tracks, script, language = self.get_album_track_infos(
            release["tracks"], release["discs"], ignored_discs, search_lang
        )
        asin_match: Optional[Match[str]] = None
        asin: Optional[str] = None
        for x in release.get("webLinks", []):
            if not x["disabled"] and match(
                "Amazon( \\((LE|RE|JP|US)\\).*)?$", x["description"]
            ):
                asin_match = search("\\/dp\\/(.+?)(\\/|$)", x["url"])
                if asin_match:
                    asin = asin_match[1]
                    break
        albumtype: str = release.get("discType", "").lower()
        albumtypes: Optional[list[str]] = [albumtype] if albumtype else None
        date: dict[str, Any] = release.get("releaseDate", {})
        year: Optional[int] = date.get("year", None)
        month: Optional[int] = date.get("month", None)
        day: Optional[int] = date.get("day", None)
        label: Optional[str] = None
        for x in release.get("artists", []):
            if "Label" in x.get("categories", ""):
                label = x["name"]
                break
        mediums: int = len(release["discs"])
        catalognum: Optional[str] = release.get("catalogNumber", None)
        genre: str = self.get_genres(release)
        media: Optional[str] = None
        try:
            media = release["discs"][0]["name"]
        except IndexError:
            pass
        data_url: str = urljoin(self.instance.base_url, f"Al/{album_id}")
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
        recording: dict[str, Any],
        index: Optional[int] = None,
        media: Optional[str] = None,
        medium: Optional[int] = None,
        medium_index: Optional[int] = None,
        medium_total: Optional[int] = None,
        search_lang: Optional[str] = None,
    ) -> TrackInfo:
        title: str = recording["name"]
        track_id: str = str(recording["id"])
        artist_categories, artist = self.get_artists(recording["artists"], self.va_string)
        artists: list[str] = []
        artists_ids: list[str] = []
        for category in artist_categories.values():
            artists.extend(
                [artist for artist in category.keys() if artist not in artists]
            )
            artists_ids.extend(
                [id for id in category.values() if id not in artists_ids]
            )
        artist_id: Optional[str] = None
        try:
            artist_id = artists_ids[0]
        except IndexError:
            pass
        arranger: str = ", ".join(artist_categories["arrangers"])
        composer: str = ", ".join(artist_categories["composers"])
        lyricist: str = ", ".join(artist_categories["lyricists"])
        length: float = recording.get("lengthSeconds", 0)
        data_url: str = urljoin(self.instance.base_url, f"S/{track_id}")
        bpm: str = str(recording.get("maxMilliBpm", 0) // 1000)
        genre: str = self.get_genres(recording)
        script, language, lyrics = self.get_lyrics(
            recording.get("lyrics", {}), search_lang
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
        tracks: list[TrackInfo],
        discs: list[dict[str, Any]],
        ignored_discs: list[int],
        search_lang: Optional[str],
    ) -> tuple[list[TrackInfo], Optional[str], Optional[str]]:
        track_infos: list[TrackInfo] = []
        script: Optional[str] = None
        language: Optional[str] = None
        for index, track in enumerate(tracks):
            if track["discNumber"] in ignored_discs or "song" not in track:
                continue
            format: str = discs[track["discNumber"] - 1]["name"]
            total: int = discs[track["discNumber"] - 1]["total"]
            track_info: TrackInfo = self.track_info(
                track["song"],
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
            for track in track_infos:
                track.script = script
                track.language = language
        return track_infos, script, language

    @staticmethod
    def get_song_fields() -> str:
        return "Artists,Tags,Bpm,Lyrics"

    @staticmethod
    def get_artists(
        artists: list[dict[str, Any]],
        va_string: str,
        include_featured_artists: bool = True,
        comp: bool = False
    ) -> tuple[dict[str, dict[str, Any]], str]:
        out: dict[str, dict[str, Any]] = {
            "producers": {},
            "circles": {},
            "vocalists": {},
            "arrangers": {},
            "composers": {},
            "lyricists": {},
        }
        is_support: list[str] = []
        for artist in artists:
            parent: dict[str, Any]
            name: str
            id: str
            if parent := artist.get("artist", {}):
                name = parent.get("name", "")
                id = str(parent.get("id", ""))
            else:
                name = artist.get("name", "")
                id = ""
            if artist["isSupport"]:
                is_support.append(id)
            categories: str = artist["categories"]
            effectiveRoles: str = artist["effectiveRoles"]
            if "Producer" in categories or "Band" in categories:
                if "Default" in artist["effectiveRoles"]:
                    artist["effectiveRoles"] += ",Arranger,Composer,Lyricist"
                    effectiveRoles = artist["effectiveRoles"]
                out["producers"][name] = id
            if "Circle" in categories:
                out["circles"][name] = id
            if "Arranger" in effectiveRoles:
                out["arrangers"][name] = id
            if "Composer" in effectiveRoles:
                out["composers"][name] = id
            if "Lyricist" in effectiveRoles:
                out["lyricists"][name] = id
            if "Vocalist" in categories:
                out["vocalists"][name] = id
        if not out["producers"] and out["vocalists"]:
            out["producers"] = out["vocalists"]
        if not out["arrangers"]:
            out["arrangers"] = out["producers"]
        if not out["composers"]:
            out["composers"] = out["producers"]
        if not out["lyricists"]:
            out["lyricists"] = out["producers"]
        if comp or len(out["producers"]) > 5:
            return out, va_string
        artistString: str = ", ".join(
            main_artist
            for main_artist, id in chain(out["producers"].items(), out["circles"].items())
            if id not in is_support
        )
        if include_featured_artists and out["vocalists"]:
            featured_artists: list[str] = [
                name
                for name, id in out["vocalists"].items()
                if name not in out["producers"] and id not in is_support
            ]
            if featured_artists:
                artistString += " feat. " + ", ".join(featured_artists)
        return out, artistString

    @staticmethod
    def get_genres(info: dict[str, Any]) -> str:
        genres: list[str] = []
        for tag in sorted(info.get("tags", {}), reverse=True, key=lambda x: x["count"]):
            if tag["tag"]["categoryName"] == "Genres":
                genres.append(tag["tag"]["name"].title())
        return "; ".join(genres)

    def get_lang(self, languages) -> str:
        if not languages:
            return "English"

        for lang in languages:
            if lang == "jp":
                return "Romaji" if self.config["prefer_romaji"].get() else "Japanese"
            if lang == "en":
                return "English"

        return "English"  # Default if no matching language found

    def get_lyrics(
        self, lyrics: list[dict[str, Any]], language: Optional[str]
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        out_script: Optional[str] = None
        out_language: Optional[str] = None
        out_lyrics: Optional[str] = None
        translated_lyrics: bool = bool(self.config["translated_lyrics"].get())
        for x in lyrics:
            if "en" in x["cultureCodes"]:
                if x["translationType"] == "Original":
                    out_script = "Latn"
                    out_language = "eng"
                if translated_lyrics or language == "English":
                    out_lyrics = x["value"]
            elif "ja" in x["cultureCodes"]:
                if x["translationType"] == "Original":
                    out_script = "Jpan"
                    out_language = "jpn"
                if not translated_lyrics and language == "Japanese":
                    out_lyrics = x["value"]
            if (
                not translated_lyrics
                and language == "Romaji"
                and x["translationType"] == "Romanized"
            ):
                out_lyrics = x["value"]
        if not out_lyrics and lyrics:
            out_lyrics = self.get_fallback_lyrics(lyrics, language)
        return out_script, out_language, out_lyrics

    @staticmethod
    def get_fallback_lyrics(
        lyrics: list[dict[str, Any]], language: Optional[str]
    ) -> Optional[str]:
        if language == "English":
            for x in lyrics:
                if "en" in x["cultureCodes"]:
                    return x["value"]
            language = "Romaji"
        if language == "Romaji":
            for x in lyrics:
                if x["translationType"] == "Romanized":
                    return x["value"]
        return lyrics[0]["value"]
