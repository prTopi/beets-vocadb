"""Things related to configuration management"""

from __future__ import annotations

from typing import TYPE_CHECKING

import msgspec
from beets import config

from beetsplug.vocadb.vocadb_api_client import ContentLanguagePreference

if TYPE_CHECKING:
    from confuse import ConfigView


LANGUAGES: list[str] | None = config["import"]["languages"].as_str_seq()
VA_NAME: str = config["va_name"].as_str()


class InstanceConfig(msgspec.Struct):
    """Stores the configuration of the plugin conveniently"""

    prefer_romaji: bool = False
    translated_lyrics: bool = False
    include_featured_album_artists: bool = False
    search_limit: int = 5
    language: ContentLanguagePreference = ContentLanguagePreference.DEFAULT

    def __post_init__(self) -> None:
        self.language = self.get_lang(self.prefer_romaji, LANGUAGES)

    # convert fields to serilizable types
    def to_dict(self) -> dict[str, int | bool | str]:
        return {
            "prefer_romaji": self.prefer_romaji,
            "translated_lyrics": self.translated_lyrics,
            "include_featured_album_artists": self.include_featured_album_artists,
            "search_limit": self.search_limit,
        }

    @classmethod
    def from_config_view(
        cls, config: ConfigView, default: InstanceConfig | None = None
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

        config.add(default.to_dict() if default else InstanceConfig().to_dict())

        return cls(
            prefer_romaji=config["prefer_romaji"].get(bool),
            translated_lyrics=config["translated_lyrics"].get(bool),
            include_featured_album_artists=config[
                "include_featured_album_artists"
            ].get(bool),
            search_limit=config["search_limit"].get(int),
        )

    @staticmethod
    def get_lang(
        prefer_romaji: bool, languages: list[str] | None
    ) -> ContentLanguagePreference:
        if languages:
            for language in languages:
                # Check for Japanese preference
                if language == "jp":
                    return (
                        ContentLanguagePreference.ROMAJI
                        if prefer_romaji
                        else ContentLanguagePreference.JAPANESE
                    )

                # Check for English preference
                if language == "en":
                    return ContentLanguagePreference.ENGLISH

        return ContentLanguagePreference.DEFAULT
