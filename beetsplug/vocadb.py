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
        pass

    def item_candidates(self, item, artist, album):
        pass

    def album_for_id(self, album_id):
        pass

    def track_for_id(self, track_id):
        self._log.debug("Searching for track {0}", track_id)
        language = self.get_lang()
        url = urljoin(
            VOCADB_API_URL,
            "songs/"
            + track_id
            + "?fields="
            + self.get_song_fields()
            + ",lang="
            + language,
        )
        # request = Request(url, headers=HEADERS)
        try:
            # with urlopen(request) as result:
            with open("/home/_/Downloads/out.json") as result:
                if result:
                    result = load(result)
                    return self.track_info(result, language=language)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return None
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return None

    def album_info(self, result, language=None):
        pass

    def track_info(
        self,
        result,
        index=None,
        medium=None,
        medium_index=None,
        medium_total=None,
        language=None,
    ):
        title = result["name"]
        track_id = result["id"]
        artist = result["artistString"]
        artist_id = None
        producers = []
        arrangers = []
        composers = []
        lyricists = []
        for x in result["artists"]:
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
        length = result["lengthSeconds"]
        data_url = urljoin(VOCADB_BASE_URL, "S/" + str(track_id))
        bpm = result["maxMilliBpm"] // 1000
        genres = []
        for x in sorted(result["tags"], key=lambda x: x["count"]):
            if x["tag"]["categoryName"] == "Genres":
                genres.append(x["tag"]["name"].title())
        genre = "; ".join(genres)
        if self.config["import_lyrics"] and "lyrics" in result and result["lyrics"]:
            lyrics = self.get_lyrics(result["lyrics"], language)
        else:
            lyrics = None
        try:
            date = datetime.fromisoformat(result["publishDate"][:-1])
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
        return "Discs,"

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

    def commands(self):
        vocadb_cmd = Subcommand("vocadb", help="vocadb testing command")

        def say_hi(lib, opts, args):
            if opts.album:
                print(self.album_for_id(args[0]))
            else:
                print(self.track_for_id(args[0]))

        vocadb_cmd.func = say_hi
        vocadb_cmd.parser.add_album_option()
        return [vocadb_cmd]
