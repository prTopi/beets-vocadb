"""Things related to configuration management"""

from dataclasses import asdict, dataclass
from typing import Optional
from confuse.core import Subview


@dataclass(frozen=True)
class InstanceConfig:
    """Stores the configuration of the plugin conveniently"""

    prefer_romaji: bool = False
    translated_lyrics: bool = False
    include_featured_album_artists: bool = False
    va_name: str = "Various artists"
    max_results: int = 5

    @classmethod
    def from_config_subview(
        cls, config: Subview, default: Optional["InstanceConfig"] = None
    ) -> "InstanceConfig":

        if default is None:
            default = cls()

        config.add(asdict(default))
        return cls(
            prefer_romaji=config["prefer_romaji"].get(bool),
            translated_lyrics=config["translated_lyrics"].get(bool),
            include_featured_album_artists=config["include_featured_album_artists"].get(
                bool
            ),
            va_name=config["va_name"].as_str(),
            max_results=config["max_results"].get(int),
        )
