from datetime import datetime
from json import load
from re import match, search
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

import beets
from beets import autotag, config, library, ui, util
from beets.autotag.hooks import AlbumInfo, TrackInfo
from beets.plugins import BeetsPlugin, apply_item_changes, get_distance


class VocaDBPlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()
        self.db_name = "VocaDB"
        self.base_url = "https://vocadb.net/"
        self.api_url = "https://vocadb.net/api/"
        self.subcommand = "vdbsync"
        self.user_agent = f"beets/{beets.__version__} +https://beets.io/"
        self.headers = {"accept": "application/json", "User-Agent": self.user_agent}
        self.config.add(
            {
                "source_weight": 0.5,
                "prefer_romaji": False,
                "translated_lyrics": False,
            }
        )

    def commands(self):
        cmd = ui.Subcommand(self.subcommand, help=f"update metadata from {self.db_name}")
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

    def func(self, lib, opts, args):
        """Command handler for the *dbsync function."""
        move = ui.should_move(opts.move)
        pretend = opts.pretend
        write = ui.should_write(opts.write)
        query = ui.decargs(args)

        self.singletons(lib, query, move, pretend, write)
        self.albums(lib, query, move, pretend, write)

    def singletons(self, lib, query, move, pretend, write):
        """Retrieve and apply info from the autotagger for items matched by
        query.
        """
        for item in lib.items(query + ["singleton:true"]):
            item_formatted = format(item)
            if not item.mb_trackid:
                self._log.info(
                    "Skipping singleton with no mb_trackid: {0}", item_formatted
                )
                continue
            if not (
                item.get("data_source") == self.db_name and item.mb_trackid.isnumeric()
            ):
                self._log.info(
                    "Skipping non-{0} singleton: {1}", self.db_name, item_formatted
                )
                continue
            track_info = self.track_for_id(item.mb_trackid)
            if not track_info:
                self._log.info(
                    "Recording ID not found: {0} for track {0}",
                    item.mb_trackid,
                    item_formatted,
                )
                continue
            with lib.transaction():
                autotag.apply_item_metadata(item, track_info)
                ui.show_model_changes(item)
                apply_item_changes(lib, item, move, pretend, write)

    def albums(self, lib, query, move, pretend, write):
        """Retrieve and apply info from the autotagger for albums matched by
        query and their items.
        """
        for album in lib.albums(query):
            album_formatted = format(album)
            if not album.mb_albumid:
                self._log.info(
                    "Skipping album with no mb_albumid: {0}", album_formatted
                )
                continue
            items = list(album.items())
            if not (
                album.get("data_source") == self.db_name and album.mb_albumid.isnumeric()
            ):
                self._log.info(
                    "Skipping non-{0} album: {1}", self.db_name, album_formatted
                )
                continue
            album_info = self.album_for_id(album.mb_albumid)
            if not album_info:
                self._log.info(
                    "Release ID {0} not found for album {1}",
                    album.mb_albumid,
                    album_formatted,
                )
                continue
            trackid_to_trackinfo = {
                track.track_id: track for track in album_info.tracks
            }
            library_trackid_to_item = {item.mb_trackid: item for item in items}
            mapping = {
                item: trackid_to_trackinfo[track_id]
                for track_id, item in library_trackid_to_item.items()
            }
            self._log.debug("applying changes to {}", album_formatted)
            with lib.transaction():
                autotag.apply_metadata(album_info, mapping)
                changed = False
                any_changed_item = items[0]
                for item in items:
                    item_changed = ui.show_model_changes(item)
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

    def track_distance(self, item, info):
        """Returns the track distance."""
        return get_distance(data_source=self.db_name, info=info, config=self.config)

    def album_distance(self, items, album_info, mapping):
        """Returns the album distance."""
        return get_distance(
            data_source=self.db_name, info=album_info, config=self.config
        )

    def candidates(self, items, artist, album, va_likely, extra_tags=None):
        self._log.debug("Searching for album {0}", album)
        url = urljoin(
            self.api_url,
            f"albums/?query={quote(album)}&maxResults=5&nameMatchMode=Auto",
        )
        request = Request(url, headers=self.headers)
        try:
            with urlopen(request) as result:
                if result:
                    result = load(result)
                    # songFields parameter doesn't exist for album search so we'll get albums by their id
                    ids = [x["id"] for x in result["items"]]
                    return [album for album in map(self.album_for_id, ids) if album]
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return []
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return []

    def item_candidates(self, item, artist, title):
        self._log.debug("Searching for track {0}", item)
        language = self.get_lang(config["import"]["languages"].as_str_seq())
        url = urljoin(
            self.api_url,
            f"songs/?query={quote(title)}"
            + f"&fields={self.get_song_fields()}"
            + f"&lang={language}"
            + "&maxResults=5&sort=SongType&preferAccurateMatches=true&nameMatchMode=Auto",
        )
        request = Request(url, headers=self.headers)
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

    def album_for_id(self, album_id):
        self._log.debug("Searching for album {0}", album_id)
        language = self.get_lang(config["import"]["languages"].as_str_seq())
        url = urljoin(
            self.api_url,
            f"albums/{album_id}"
            + "?fields=Artists,Discs,Tags,Tracks,WebLinks"
            + f"&songFields={self.get_song_fields()}"
            + f"&lang={language}",
        )
        request = Request(url, headers=self.headers)
        try:
            with urlopen(request) as result:
                if result:
                    result = load(result)
                    return self.album_info(result, search_lang=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return

    def track_for_id(self, track_id):
        self._log.debug("Searching for track {0}", track_id)
        language = self.get_lang(config["import"]["languages"].as_str_seq())
        url = urljoin(
            self.api_url,
            f"songs/{track_id}"
            + f"?fields={self.get_song_fields()}"
            + f"&lang={language}",
        )
        request = Request(url, headers=self.headers)
        try:
            with urlopen(request) as result:
                if result:
                    result = load(result)
                    return self.track_info(result, search_lang=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return

    def album_info(self, release, search_lang=None):
        discs = len(set([x["discNumber"] for x in release["tracks"]]))
        if not release["discs"]:
            release["discs"] = [
                {"discNumber": x + 1, "name": "CD", "mediaType": "Audio"}
                for x in range(discs)
            ]
        ignored_discs = []
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

        va = release.get("discType", "") == "Compilation"
        album = release["name"]
        album_id = str(release["id"])
        artist_categories, artist = self.get_artists(
            release["artists"], album=True, comp=va
        )
        if artist == "Various artists":
            va = True
        artists = []
        artists_ids = []
        for category in artist_categories.values():
            artists.extend(
                [artist for artist in category.keys() if artist not in artists]
            )
            artists_ids.extend(
                [id for id in category.values() if id not in artists_ids]
            )
        try:
            artist_id = artists_ids[0]
        except IndexError:
            artist_id = None
        tracks, script, language = self.get_album_track_infos(
            release["tracks"], release["discs"], ignored_discs, search_lang
        )
        asin = None
        for x in release.get("webLinks", []):
            if not x["disabled"] and match(
                "Amazon( \\((LE|RE|JP|US)\\).*)?$", x["description"]
            ):
                asin = search("\\/dp\\/(.+?)(\\/|$)", x["url"])
                if asin:
                    asin = asin[1]
                    break
        albumtype = release.get("discType", "").lower()
        albumtypes = [albumtype]
        date = release.get("releaseDate", {})
        year = date.get("year", None)
        month = date.get("month", None)
        day = date.get("day", None)
        label = None
        for x in release.get("artists", []):
            if "Label" in x.get("categories", ""):
                label = x["name"]
                break
        mediums = len(release["discs"])
        catalognum = release.get("catalogNumber", None)
        genre = self.get_genres(release)
        try:
            media = release["discs"][0]["name"]
        except IndexError:
            media = None
        data_url = urljoin(self.base_url, f"Al/{album_id}")
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
            data_source=self.db_name,
            data_url=data_url,
        )

    def track_info(
        self,
        recording,
        index=None,
        media=None,
        medium=None,
        medium_index=None,
        medium_total=None,
        search_lang=None,
    ):
        title = recording["name"]
        track_id = str(recording["id"])
        artist_categories, artist = self.get_artists(recording["artists"])
        artists = []
        artists_ids = []
        for category in artist_categories.values():
            artists.extend(
                [artist for artist in category.keys() if artist not in artists]
            )
            artists_ids.extend(
                [id for id in category.values() if id not in artists_ids]
            )
        try:
            artist_id = artists_ids[0]
        except IndexError:
            artist_id = None
        arranger = ", ".join(artist_categories["arrangers"])
        composer = ", ".join(artist_categories["composers"])
        lyricist = ", ".join(artist_categories["lyricists"])
        length = recording.get("lengthSeconds", 0)
        data_url = urljoin(self.base_url, f"S/{track_id}")
        bpm = str(recording.get("maxMilliBpm", 0) // 1000)
        genre = self.get_genres(recording)
        script, language, lyrics = self.get_lyrics(
            recording.get("lyrics", {}), search_lang
        )
        if "publishDate" in recording:
            date = datetime.fromisoformat(recording["publishDate"][:-1])
            original_day = date.day
            original_month = date.month
            original_year = date.year
        else:
            original_day = None
            original_month = None
            original_year = None
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
            data_source=self.db_name,
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

    def get_album_track_infos(self, tracks, discs, ignored_discs, search_lang):
        track_infos = []
        script = None
        language = None
        for index, track in enumerate(tracks):
            if track["discNumber"] in ignored_discs or "song" not in track:
                continue
            format = discs[track["discNumber"] - 1]["name"]
            total = discs[track["discNumber"] - 1]["total"]
            track_info = self.track_info(
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

    def get_song_fields(self):
        return "Artists,Tags,Bpm,Lyrics"

    def get_artists(self, artists, album=False, comp=False):
        out = {
            "producers": {},
            "circles": {},
            "vocalists": {},
            "arrangers": {},
            "composers": {},
            "lyricists": {},
        }
        for artist in artists:
            parent = artist.get("artist", {})
            if parent:
                name = parent.get("name", "")
                id = str(parent.get("id", ""))
            else:
                name = artist.get("name", "")
                id = ""
            if "Producer" in artist["categories"] or "Band" in artist["categories"]:
                if "Default" in artist["effectiveRoles"]:
                    artist["effectiveRoles"] += ",Arranger,Composer,Lyricist"
                out["producers"][name] = id
            if "Circle" in artist["categories"]:
                out["circles"][name] = id
            if "Arranger" in artist["effectiveRoles"]:
                out["arrangers"][name] = id
            if "Composer" in artist["effectiveRoles"]:
                out["composers"][name] = id
            if "Lyricist" in artist["effectiveRoles"]:
                out["lyricists"][name] = id
            if "Vocalist" in artist["categories"] and not artist["isSupport"]:
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
            return out, "Various artists"
        artistString = ", ".join(
            list(out["producers"].keys()) + list(out["circles"].keys())
        )
        if not album and out["vocalists"]:
            featuring = [
                name for name in out["vocalists"] if name not in out["producers"]
            ]
            if featuring:
                artistString += " feat. " + ", ".join(featuring)
        return out, artistString

    def get_genres(self, info):
        genres = []
        for tag in sorted(info.get("tags", {}), reverse=True, key=lambda x: x["count"]):
            if tag["tag"]["categoryName"] == "Genres":
                genres.append(tag["tag"]["name"].title())
        return "; ".join(genres)

    def get_lang(self, languages):
        if languages:
            for x in languages:
                if x == "jp":
                    if self.config["prefer_romaji"]:
                        return "Romaji"
                    return "Japanese"
                if x == "en":
                    return "English"
        return "English"

    def get_lyrics(self, lyrics, language):
        out_script = None
        out_language = None
        out_lyrics = None
        for x in lyrics:
            if "en" in x["cultureCodes"]:
                if x["translationType"] == "Original":
                    out_script = "Latn"
                    out_language = "eng"
                if self.config["translated_lyrics"] or language == "English":
                    out_lyrics = x["value"]
            elif "ja" in x["cultureCodes"]:
                if x["translationType"] == "Original":
                    out_script = "Jpan"
                    out_language = "jpn"
                if not self.config["translated_lyrics"] and language == "Japanese":
                    out_lyrics = x["value"]
            if (
                not self.config["translated_lyrics"]
                and language == "Romaji"
                and x["translationType"] == "Romanized"
            ):
                out_lyrics = x["value"]
        if not out_lyrics and lyrics:
            out_lyrics = self.get_fallback_lyrics(lyrics, language)
        return out_script, out_language, out_lyrics

    def get_fallback_lyrics(self, lyrics, language):
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
