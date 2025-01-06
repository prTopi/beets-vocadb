"""Things related to configuration management"""

from attrs import asdict, define
from confuse.core import Subview


@define
class InstanceConfig:
    """Stores the configuration of the plugin conveniently"""

    prefer_romaji: bool = False
    translated_lyrics: bool = False
    include_featured_album_artists: bool = False
    max_results: int = 5

    @classmethod
    def from_config_subview(
        cls, config: Subview, default: "InstanceConfig | None" = None
    ) -> "InstanceConfig":
        """Creates an InstanceConfig from a configuration subview.

        Args:
            config: A Subview object containing configuration values
            default: Optional default InstanceConfig to use as base values.
                    If None, creates a new default instance.

        Returns:
            A new InstanceConfig instance populated with values from the config,
            falling back to defaults when values are missing.
        """

        config.add(asdict(default or cls()))

        return cls(
            prefer_romaji=config["prefer_romaji"].get(bool),
            translated_lyrics=config["translated_lyrics"].get(bool),
            include_featured_album_artists=config["include_featured_album_artists"].get(
                bool
            ),
            max_results=config["max_results"].get(int),
        )
