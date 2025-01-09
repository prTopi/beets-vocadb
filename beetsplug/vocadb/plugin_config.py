"""Things related to configuration management"""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec

if TYPE_CHECKING:
    from confuse.core import Subview


class InstanceConfig(msgspec.Struct):
    """Stores the configuration of the plugin conveniently"""

    prefer_romaji: bool = False
    translated_lyrics: bool = False
    include_featured_album_artists: bool = False
    max_results: int = 5

    @classmethod
    def from_config_subview(
        cls, config: Subview, default: InstanceConfig | None = None
    ) -> InstanceConfig:
        """Creates an InstanceConfig from a configuration subview.

        Args:
            config: A Subview object containing configuration values
            default: Optional default InstanceConfig to use as base values.
                    If None, creates a new default instance.

        Returns:
            A new InstanceConfig instance populated with values from the config, falling
            back to defaults when values are missing.
        """

        fallback: dict[str, bool | int] = msgspec.structs.asdict(
            default or cls()
        )

        config.add(fallback)

        return cls(
            prefer_romaji=config["prefer_romaji"].get(bool),
            translated_lyrics=config["translated_lyrics"].get(bool),
            include_featured_album_artists=config[
                "include_featured_album_artists"
            ].get(bool),
            max_results=config["max_results"].get(int),
        )
