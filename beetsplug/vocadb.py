from datetime import datetime
from json import load
from re import match, search
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

import beets
from beets import config
from beets.autotag.hooks import AlbumInfo, TrackInfo
from beets.importer import action
from beets.plugins import BeetsPlugin, get_distance

VOCADB_NAME = "VocaDB"
VOCADB_BASE_URL = "https://vocadb.net/"
VOCADB_API_URL = "https://vocadb.net/api/"
USER_AGENT = f"beets/{beets.__version__} +https://beets.io/"
HEADERS = {"accept": "application/json", "User-Agent": USER_AGENT}


class VocaDBPlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()
        self.config.add(
            {
                "source_weight": 0.5,
                "prefer_romaji": False,
            }
        )
        self.register_listener("import_task_choice", self.update_names)

    def update_names(self, task, session):
        """Updates names to the prefered language

        We do it in an event to preserve distance while respecting language settings
        """
        if task.choice_flag in (action.SKIP, action.ASIS):
            return
        for candidate in task.candidates:
            if candidate.info["data_source"] == VOCADB_NAME:
                candidate.info["album"] = candidate.info.pop("newname")
                for track in candidate.info["tracks"]:
                    track["title"] = track.pop("newname")

    def track_distance(self, item, info):
        """Returns the track distance."""
        return get_distance(data_source=VOCADB_NAME, info=info, config=self.config)

    def album_distance(self, items, album_info, mapping):
        """Returns the album distance."""
        return get_distance(
            data_source=VOCADB_NAME, info=album_info, config=self.config
        )

    def candidates(self, items, artist, album, va_likely, extra_tags=None):
        self._log.debug("Searching for album {0}", album)
        url = urljoin(
            VOCADB_API_URL,
            "albums/?query=" + quote(album) + "&maxResults=5&nameMatchMode=Auto",
        )
        request = Request(url, headers=HEADERS)
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
            VOCADB_API_URL,
            "songs/?query="
            + quote(title)
            + "&fields="
            + self.get_song_fields()
            + "&lang="
            + language
            + "&maxResults=5&sort=SongType&preferAccurateMatches=true&nameMatchMode=Auto",
        )
        request = Request(url, headers=HEADERS)
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
            VOCADB_API_URL,
            "albums/"
            + str(album_id)
            + "?fields=Artists,Discs,Tags,Tracks,WebLinks"
            + "&songFields="
            + self.get_song_fields()
            + "&lang="
            + language,
        )
        request = Request(url, headers=HEADERS)
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
            VOCADB_API_URL,
            "songs/"
            + str(track_id)
            + "?fields="
            + self.get_song_fields()
            + "&lang="
            + language,
        )
        request = Request(url, headers=HEADERS)
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
                {"discNumber": x + 1, "name": "CD", "mediaType": "Album"}
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

        album = release["defaultName"]
        newname = release["name"]
        album_id = str(release["id"])
        artist = release["artistString"].split(" feat. ", maxsplit=1)[0]
        if "artists" in release and release["artists"]:
            artist_id = str(release["artists"][0]["artist"]["id"])
        else:
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
        va = release.get("artistString", "") == "Various artists"
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
        if release["discs"]:
            media = release["discs"][0]["name"]
        else:
            media = None
        data_url = urljoin(VOCADB_BASE_URL, "Al/" + album_id)
        return AlbumInfo(
            album=album,
            newname=newname,
            album_id=album_id,
            artist=artist,
            artist_id=artist_id,
            tracks=tracks,
            asin=asin,
            albumtype=albumtype,
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
            data_source=VOCADB_NAME,
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
        title = recording["defaultName"]
        newname = recording["name"]
        track_id = str(recording["id"])
        artists, artist_id = self.get_artists(recording["artists"])
        if recording["artistString"] == "Various artists":
            artist = ", ".join(artists["producers"])
            if artists["vocalists"]:
                artist += " feat. " + ", ".join(artists["vocalists"])
        elif (
            recording["artistString"].endswith(" feat. various")
            and artists["vocalists"]
        ):
            artist = (
                recording["artistString"].split(" feat. ", maxsplit=1)[0]
                + " feat. "
                + ", ".join(artists["vocalists"])
            )
        else:
            artist = recording["artistString"]
        if not artists["arrangers"]:
            artists["arrangers"] = artists["producers"]
        arranger = ", ".join(artists["arrangers"])
        if not artists["composers"]:
            artists["composers"] = artists["producers"]
        composer = ", ".join(artists["composers"])
        if not artists["lyricists"]:
            artists["lyricists"] = artists["producers"]
        lyricist = ", ".join(artists["lyricists"])
        length = recording.get("lengthSeconds", 0)
        data_url = urljoin(VOCADB_BASE_URL, "S/" + track_id)
        bpm = recording.get("maxMilliBpm", 0) // 1000
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
            newname=newname,
            track_id=track_id,
            artist=artist,
            artist_id=artist_id,
            length=length,
            index=index,
            media=media,
            medium=medium,
            medium_index=medium_index,
            medium_total=medium_total,
            data_source=VOCADB_NAME,
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
        index = 0
        for track in tracks:
            index += 1
            if track["discNumber"] in ignored_discs or "song" not in track:
                continue
            format = discs[track["discNumber"] - 1]["name"]
            total = discs[track["discNumber"] - 1]["total"]
            track_info = self.track_info(
                track["song"],
                index=index,
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

    def get_artists(self, artists):
        artist_id = None
        out_artists = {
            "producers": [],
            "vocalists": [],
            "arrangers": [],
            "composers": [],
            "lyricists": [],
        }
        for x in artists:
            if "Producer" in x["categories"]:
                if not artist_id:
                    artist_id = x.get("artist", {}).get("id", None)
                out_artists["producers"].append(x["name"])
            if "Arranger" in x["effectiveRoles"]:
                out_artists["arrangers"].append(x["name"])
            if "Composer" in x["effectiveRoles"]:
                out_artists["composers"].append(x["name"])
            if "Lyricist" in x["effectiveRoles"]:
                out_artists["lyricists"].append(x["name"])
            if "Vocalist" in x["categories"] and not x["isSupport"]:
                out_artists["vocalists"].append(x["name"])
        if artist_id:
            artist_id = str(artist_id)
        return out_artists, artist_id

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
                if language == "English":
                    out_lyrics = x["value"]
            elif "ja" in x["cultureCodes"]:
                if x["translationType"] == "Original":
                    out_script = "Jpan"
                    out_language = "jpn"
                if language == "Japanese":
                    out_lyrics = x["value"]
            if language == "Romaji" and x["translationType"] == "Romanized":
                out_lyrics = x["value"]
        if not out_lyrics and lyrics:
            out_lyrics = self.get_fallback_lyrics(lyrics, language)
        return out_script, out_language, out_lyrics

    def get_fallback_lyrics(self, lyrics, language):
        if language == "English":
            for x in lyrics:
                if "en" in x["cultureCode"]:
                    return x["value"]
            return self.get_fallback_lyrics(lyrics, "Romaji")
        if language == "Romaji":
            for x in lyrics:
                if x["translationType"] == "Romanized":
                    return x["value"]
        return lyrics[0]["value"]
