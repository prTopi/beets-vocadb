from datetime import datetime
from json import load
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
        for match in task.candidates:
            if match.info["data_source"] == VOCADB_NAME:
                match.info["album"] = match.info.pop("newname")
                for track in match.info["tracks"]:
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

    def item_candidates(self, item, artist, album):
        self._log.debug("Searching for track {0}", item)
        language = self.get_lang(config["import"]["languages"])
        url = urljoin(
            VOCADB_API_URL,
            "songs/?query="
            + quote(item)
            + "&fields="
            + self.get_song_fields()
            + "&lang="
            + language
            + "&maxResults=5&nameMatchMode=Auto",
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
        language = self.get_lang(config["import"]["languages"])
        url = urljoin(
            VOCADB_API_URL,
            "albums/"
            + str(album_id)
            + "?fields=Artists,Discs,Tags,Tracks"
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
        language = self.get_lang(config["import"]["languages"])
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
        if "discs" not in release or not release["discs"]:
            release["discs"] = [{"discNumber": 1, "name": "CD", "mediaType": "Album"}]
        ignored_discs = []
        for x in release["discs"]:
            if x["mediaType"] == "Video" and config["match"]["ignore_video_tracks"]:
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
        album_id = release["id"]
        artist = release["artistString"].split(" feat. ", maxsplit=1)[0]
        if "artists" in release and release["artists"]:
            artist_id = release["artists"][0]["artist"]["id"]
        else:
            artist_id = None
        tracks, script, language = self.get_album_track_infos(
            release["tracks"], release["discs"], ignored_discs, search_lang
        )
        albumtype = release["discType"]
        va = release["artistString"] == "Various artists"
        year = release["releaseDate"]["year"]
        month = release["releaseDate"]["month"]
        day = release["releaseDate"]["day"]
        label = None
        for x in release["artists"]:
            if "Label" in x["categories"]:
                label = x["name"]
                break
        mediums = len(release["discs"])
        catalognum = release["catalogNumber"]
        genre = self.get_genres(release)
        media = release["discs"][0]["name"]
        data_url = urljoin(VOCADB_BASE_URL, "Al/" + str(album_id))
        return AlbumInfo(
            album=album,
            newname=newname,
            album_id=album_id,
            artist=artist,
            artist_id=artist_id,
            tracks=tracks,
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
        track_id = recording["id"]
        artist = recording[
            "artistString"
        ]  # TODO: Feat. shortened to various. Maybe read from artists tag?
        producers, arrangers, composers, lyricists, artist_id = self.get_producers(
            recording["artists"]
        )
        if arrangers:
            arranger = ", ".join(arrangers)
        else:
            arranger = ", ".join(producers)
        if composers:
            composer = ", ".join(composers)
        else:
            composer = ", ".join(producers)
        if lyricists:
            lyricist = ", ".join(lyricists)
        else:
            lyricist = ", ".join(producers)
        length = recording["lengthSeconds"]
        data_url = urljoin(VOCADB_BASE_URL, "S/" + str(track_id))
        if "maxMilliBpm" in recording:
            bpm = recording["maxMilliBpm"] // 1000
        else:
            bpm = 0
        genre = self.get_genres(recording)
        if "lyrics" in recording:
            script, language, lyrics = self.get_lyrics(recording["lyrics"], search_lang)
        else:
            script = language = lyrics = None
        date = datetime.fromisoformat(recording["publishDate"][:-1])
        original_day = date.day
        original_month = date.month
        original_year = date.year
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
            if track["discNumber"] in ignored_discs:
                continue
            format = discs[track["discNumber"] - 1]["name"]
            total = discs[track["discNumber"] - 1]["total"]
            track_info = self.track_info(
                track["song"],
                index=index,
                media=format,
                medium=track["discNumber"],
                medium_index=track["trackNumber"],
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

    def get_producers(self, artists):
        artist_id = None
        producers = []
        arrangers = []
        composers = []
        lyricists = []
        for x in artists:
            if "Producer" in x["categories"]:
                if not artist_id:
                    artist_id = x["artist"]["id"]
                producers.append(x["name"])
                if "Arranger" in x["effectiveRoles"]:
                    arrangers.append(x["name"])
                if "Composer" in x["effectiveRoles"]:
                    composers.append(x["name"])
                if "Lyricist" in x["effectiveRoles"]:
                    lyricists.append(x["name"])
        return producers, arrangers, composers, lyricists, artist_id

    def get_genres(self, info):
        genres = []
        if "tags" in info:
            for tag in sorted(info["tags"], reverse=True, key=lambda x: x["count"]):
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
            if x["cultureCode"] == "en":
                if x["translationType"] == "Original":
                    out_script = "Latn"
                    out_language = "eng"
                if language == "English":
                    out_lyrics = x["value"]
            elif x["cultureCode"] == "ja":
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
                if x["cultureCode"] == "en":
                    return x["value"]
            return self.get_fallback_lyrics(lyrics, "Romaji")
        if language == "Romaji":
            for x in lyrics:
                if x["translationType"] == "Romanized":
                    return x["value"]
        return lyrics[0]["value"]
