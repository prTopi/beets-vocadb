"""Things related to configuration management"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import msgspec
from beets import config

if not sys.version_info < (3, 11):
    from enum import StrEnum  # pyright: ignore[reportUnreachable]
else:
    from .requests_handler import StrEnum

if TYPE_CHECKING:
    from confuse.core import Subview

LANGUAGES: list[str] | None = config["import"]["languages"].as_str_seq()
VA_NAME: str = config["va_name"].as_str()


class LanguagePreference(StrEnum):
    ENGLISH = "English"
    JAPANESE = "Japanese"
    ROMAJI = "Romaji"

    DEFAULT = ENGLISH

    @classmethod
    def from_config(
        cls, prefer_romaji: bool, languages: list[str] | None = LANGUAGES
    ) -> LanguagePreference:
        if not languages:
            return cls.DEFAULT

        for language in languages:
            # Check for Japanese preference
            if language == "jp":
                return cls.ROMAJI if prefer_romaji else cls.JAPANESE

            # Check for English preference
            if language == "en":
                return cls.ENGLISH

        return cls.DEFAULT


class InstanceConfig(msgspec.Struct):
    """Stores the configuration of the plugin conveniently"""

    prefer_romaji: bool = False
    translated_lyrics: bool = False
    include_featured_album_artists: bool = False
    max_results: int = 5
    _language: LanguagePreference = LanguagePreference.DEFAULT

    def __post_init__(self) -> None:
        self._language = LanguagePreference.from_config(self.prefer_romaji)

    @property
    def language(self) -> str:
        return self._language.value

    # just in case
    @language.setter
    def language(self, value: str) -> None:
        self._language = LanguagePreference(value)

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
