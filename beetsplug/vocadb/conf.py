"""Things related to configuration management"""

from confuse import AttrDict
from confuse.core import Subview


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

DEFAULT_CONFIG: ConfigDict = ConfigDict(
    prefer_romaji=False,
    translated_lyrics=False,
    include_featured_album_artists=False,
    va_name="Various artists",
    max_results=5,
)

def get_config(config: Subview) -> ConfigDict:
    return ConfigDict(
        prefer_romaji=config["prefer_romaji"].get(bool),
        translated_lyrics=config["translated_lyrics"].get(bool),
        include_featured_album_artists=config[
            "include_featured_album_artists"
        ].get(bool),
        va_name=config["va_name"].as_str(),
        max_results=config["max_results"].get(int),
    )
