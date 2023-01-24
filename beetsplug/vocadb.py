from json import load
from urllib.error import HTTPError
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

import beets
from beets import config
from beets.autotag.hooks import AlbumInfo, TrackInfo
from beets.plugins import BeetsPlugin, MetadataSourcePlugin, get_distance
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
                "prefer_romaji": True,
                "no_empty_roles": True,
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
        url = urljoin(
            VOCADB_API_URL,
            "songs/"
            + track_id
            + "?fields="
            + self.get_song_fields()
            + ",lang="
            + self.get_lang(),
        )
        # request = Request(url, headers=HEADERS)
        try:
            # with urlopen(request) as result:
            with open("/home/_/Downloads/out.json") as result:
                if result:
                    result = load(result)
                    return self.track_info(result)
                else:
                    self._log.debug("API Error: Returned empty page (query: {0})", url)
                    return None
        except HTTPError as e:
            self._log.debug("API Error: {0} (query: {1})", e, url)
            return None

    def album_info(self, result):
        pass

    def track_info(
        self, result, index=None, medium=None, medium_index=None, medium_total=None
    ):
        title = result["name"]
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
        if arrangers:
            arranger = ", ".join(arrangers)
        elif self.config["no_empty_roles"]:
            arranger = ", ".join(producers)
        if composers:
            composer = ", ".join(composers)
        elif self.config["no_empty_roles"]:
            composer = ", ".join(producers)
        if lyricists:
            lyricist = ", ".join(lyricists)
        elif self.config["no_empty_roles"]:
            lyricist = ", ".join(producers)
        track_id = result["id"]
        length = result["lengthSeconds"]
        data_url = urljoin(VOCADB_BASE_URL, "S/" + str(track_id))
        bpm = result["maxMilliBpm"] // 1000
        genres = []
        for x in sorted(result["tags"], key=lambda x: x["count"]):
            if x["tag"]["categoryName"] == "Genres":
                genres.append(x["tag"]["name"].title())
        genre = "; ".join(genres)
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
            data_souce="VocaDB",
            data_url=data_url,
            lyricist=lyricist,
            composer=composer,
            arranger=arranger,
            bpm=bpm,
            genre=genre,
        )

    def get_album_fields(self):
        return "Discs,"

    def get_song_fields(self):
        return "Artists,Lyrics,Tags,Bpm"

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
