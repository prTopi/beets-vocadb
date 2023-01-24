from datetime import datetime
from json import load
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

import beets
from beets import config
from beets.autotag.hooks import AlbumInfo, TrackInfo
from beets.plugins import BeetsPlugin, get_distance
from beets.ui import Subcommand

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
                "import_lyrics": False,
                "prefer_romaji": True,
                "no_empty_roles": False,
            }
        )

    def track_distance(self, item, info):
        """Returns the track distance."""
        return get_distance(data_source="VocaDB", info=info, config=self.config)

    def album_distance(self, items, album_info, mapping):
        """Returns the album distance."""
        return get_distance(data_source="VocaDB", info=album_info, config=self.config)

    def candidates(self, items, artist, album, va_likely, extra_tags=None):
        self._log.debug("Searching for album {0}", album)
        language = self.get_lang()
        url = urljoin(
            VOCADB_API_URL,
            "albums/?query="
            + quote(album)
            + "&fields="
            + self.get_album_fields()
            + "&songFields="
            + self.get_song_fields()
            + "&lang="
            + language
            + "&maxResults=5",
        )
        request = Request(url, headers=HEADERS)
        try:
            with urlopen(request) as result:
                # with open("/home/topi/Downloads/out-search-album.json") as result:
                if result:
                    result = load(result)
                    return [
                        album
                        for album in map(self.album_info, result["items"])
                        if album
                    ]
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return []
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return []

    def item_candidates(self, item, artist, album):
        self._log.debug("Searching for track {0}", item)
        language = self.get_lang()
        url = urljoin(
            VOCADB_API_URL,
            "songs/?query="
            + quote(item)
            + "&fields="
            + self.get_song_fields()
            + "&lang="
            + language
            + "&maxResults=5",
        )
        request = Request(url, headers=HEADERS)
        try:
            with urlopen(request) as result:
                # with open("/home/topi/Downloads/out-search-album.json") as result:
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
        language = self.get_lang()
        url = urljoin(
            VOCADB_API_URL,
            "albums/"
            + album_id
            + "?fields="
            + self.get_album_fields()
            + "&songFields="
            + self.get_song_fields()
            + "&lang="
            + language,
        )
        request = Request(url, headers=HEADERS)
        try:
            with urlopen(request) as result:
                # with open("/home/topi/Downloads/out-album.json") as result:
                if result:
                    result = load(result)
                    return self.album_info(result, language=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return

    def track_for_id(self, track_id):
        self._log.debug("Searching for track {0}", track_id)
        language = self.get_lang()
        url = urljoin(
            VOCADB_API_URL,
            "songs/"
            + track_id
            + "?fields="
            + self.get_song_fields()
            + "&lang="
            + language,
        )
        request = Request(url, headers=HEADERS)
        try:
            with urlopen(request) as result:
                # with open("/home/topi/Downloads/out-track.json") as result:
                if result:
                    result = load(result)
                    return self.track_info(result, language=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return

    def album_info(self, release, language=None):
        if "discs" not in release or not release["discs"]:
            release["discs"] = [{"discNumber": 1, "name": "CD"}]
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

        track_infos = []
        index = 0
        for track in release["tracks"]:
            index += 1
            if track["discNumber"] in ignored_discs:
                continue
            format = release["discs"][track["discNumber"] - 1]["name"]
            total = release["discs"][track["discNumber"] - 1]["total"]
            track_info = self.track_info(
                track["song"],
                index=index,
                media=format,
                medium=track["discNumber"],
                medium_index=track["trackNumber"],
                medium_total=total,
                language=language,
            )
            track_infos.append(track_info)

        album = release["name"]
        album_id = release["id"]
        artist = release["artistString"]
        if "artists" in release and release["artists"]:
            artist_id = release["artists"][0]["artist"]["id"]
        else:
            artist_id = None
        tracks = track_infos
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
        genres = []
        if "tags" in release:
            for x in sorted(release["tags"], key=lambda x: x["count"]):
                if x["tag"]["categoryName"] == "Genres":
                    genres.append(x["tag"]["name"].title())
        genre = "; ".join(genres)
        albumstatus = release["status"]
        media = release["discs"][0]["name"]
        data_url = urljoin(VOCADB_BASE_URL, "Al/" + str(album_id))
        return AlbumInfo(
            album=album,
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
            genre=genre,
            albumstatus=albumstatus,
            media=media,
            data_source="VocaDB",
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
        language=None,
    ):
        title = recording["name"]
        track_id = recording["id"]
        artist = recording[
            "artistString"
        ]  # TODO: Feat. shortened to various. Maybe read from artists tag?
        artist_id = None
        producers = []
        arrangers = []
        composers = []
        lyricists = []
        if "artist" in recording and recording["artists"]:
            for x in recording["artists"]:
                if "Producer" in x["categories"]:
                    if not artist_id:
                        if "artist" in x and "id" in x["artist"]:
                            artist_id = x["artist"]["id"]
                        else:
                            artist_id = x["id"]
                    producers.append(x["name"])
                    if "Arranger" in x["effectiveRoles"]:
                        arrangers.append(x["name"])
                    if "Composer" in x["effectiveRoles"]:
                        composers.append(x["name"])
                    if "Lyricist" in x["effectiveRoles"]:
                        lyricists.append(x["name"])
        arranger = ", ".join(arrangers)
        if not arranger and self.config["no_empty_roles"]:
            arranger = ", ".join(producers)
        composer = ", ".join(composers)
        if not composer and self.config["no_empty_roles"]:
            composer = ", ".join(producers)
        lyricist = ", ".join(lyricists)
        if not lyricist and self.config["no_empty_roles"]:
            lyricist = ", ".join(producers)
        length = recording["lengthSeconds"]
        data_url = urljoin(VOCADB_BASE_URL, "S/" + str(track_id))
        if "maxMilliBpm" in recording:
            bpm = recording["maxMilliBpm"] // 1000
        else:
            bpm = 0
        genres = []
        if "tags" in recording:
            for x in sorted(recording["tags"], key=lambda x: x["count"]):
                if x["tag"]["categoryName"] == "Genres":
                    genres.append(x["tag"]["name"].title())
        genre = "; ".join(genres)
        if (
            self.config["import_lyrics"]
            and "lyrics" in recording
            and recording["lyrics"]
        ):
            lyrics = self.get_lyrics(recording["lyrics"], language)
        else:
            lyrics = None
        try:
            date = datetime.fromisoformat(recording["publishDate"][:-1])
        except ValueError as e:
            self._log.debug("Date Error: {0}", e)
            original_day = original_month = original_year = None
        else:
            original_day = date.day
            original_month = date.month
            original_year = date.year
        return TrackInfo(
            title=title,
            track_id=track_id,
            artist=artist,
            artist_id=artist_id,
            length=length,
            index=index,
            media=media,
            medium=medium,
            medium_index=medium_index,
            medium_total=medium_total,
            data_source="VocaDB",
            data_url=data_url,
            lyricist=lyricist,
            composer=composer,
            arranger=arranger,
            bpm=bpm,
            genre=genre,
            lyrics=lyrics,
            original_day=original_day,
            original_month=original_month,
            original_year=original_year,
        )

    def get_album_fields(self):
        return "Artists,Discs,Tags,Tracks"

    def get_song_fields(self):
        fields = "Artists,Tags,Bpm"
        if self.config["import_lyrics"]:
            fields += "Lyrics"
        return fields

    def get_lang(self):
        if config["import"]["languages"]:
            for x in config["import"]["languages"]:
                if x == "jp":
                    if self.config["prefer_romaji"]:
                        return "Romaji"
                    return "Japanese"
                if x == "en":
                    return "English"
        return "English"

    def get_lyrics(self, lyrics, language):
        if language == "English":
            for x in lyrics:
                if x["cultureCode"] == "en":
                    return x["value"]
            return self.get_lyrics(lyrics, "Romaji")
        if language == "Romaji":
            for x in lyrics:
                if x["translationType"] == "Romanized":
                    return x["value"]
        return lyrics[0]["value"]
