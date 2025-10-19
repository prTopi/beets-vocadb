from __future__ import annotations

from typing import TYPE_CHECKING

from beetsplug.vocadb.vocadb_api_client import (
    ContentLanguagePreference,
    TranslationType,
)

if TYPE_CHECKING:
    from beetsplug.vocadb.vocadb_api_client import LyricsForSongContract


class LyricsProcessor:
    def __init__(self, language_preference: str) -> None:
        self.language_preference: str = language_preference

    def get_lyrics(
        self,
        remote_lyrics_list: tuple[LyricsForSongContract, ...] | None,
    ) -> tuple[str | None, str | None, str | None]:
        """Extract lyrics information with language and script metadata.

        Processes available lyrics versions to select the most appropriate one
        based on user language preferences and translation type. Also determines
        the script system and language code for the selected lyrics.

        Args:
            remote_lyrics_list: List of lyrics data from VocaDB API

        Returns:
            Tuple containing:
            - Script code (e.g., "Latn", "Jpan", "Qaaa" for multiple scripts)
            - Language code (e.g., "eng", "jpn", "mul" for multiple languages)
            - Lyrics text content
        """
        script: str | None = None
        language: str | None = None
        lyrics: str | None = None

        remote_lyrics: LyricsForSongContract
        if remote_lyrics_list:
            for remote_lyrics in remote_lyrics_list:
                remote_translation_type: TranslationType = (
                    remote_lyrics.translation_type
                )
                value: str | None = remote_lyrics.value
                # get the intersection
                culture_codes: set[str] | None = remote_lyrics.culture_codes
                if culture_codes:
                    culture_codes &= {
                        "en",
                        "ja",
                    }

                if not culture_codes:
                    if (
                        self.language_preference
                        == ContentLanguagePreference.ROMAJI
                        and remote_translation_type == TranslationType.ROMANIZED
                    ):
                        lyrics = value
                    continue

                if "en" in culture_codes:
                    if remote_translation_type == TranslationType.ORIGINAL:
                        script = "Latn"
                        language = "eng"
                    if (
                        self.language_preference
                        == ContentLanguagePreference.ENGLISH
                    ):
                        lyrics = value
                    continue

                if "ja" in culture_codes:
                    if remote_translation_type == TranslationType.ORIGINAL:
                        script = "Jpan"
                        language = "jpn"
                    if (
                        self.language_preference
                        == ContentLanguagePreference.JAPANESE
                    ):
                        lyrics = value

            if not lyrics and remote_lyrics_list:
                lyrics = self._get_fallback_lyrics(
                    remote_lyrics_list,
                )

        return script, language, lyrics

    def _get_fallback_lyrics(
        self,
        remote_lyrics_list: tuple[LyricsForSongContract, ...],
    ) -> str | None:
        """Internal fallback mechanism when preferred lyrics are not available.

        Implements a fallback strategy for lyrics selection when the user's
        preferred language/translation type combination is not available.
        Falls back through English, Romanized, and finally Original lyrics.

        Args:
            remote_lyrics_list: List of available lyrics data

        Returns:
            Lyrics text from the best available fallback option, or None if none
            found
        """
        language_preference = self.language_preference
        remote_lyrics: LyricsForSongContract
        if language_preference == ContentLanguagePreference.ENGLISH:
            for remote_lyrics in remote_lyrics_list:
                culture_codes: set[str] | None
                if (
                    culture_codes := remote_lyrics.culture_codes
                ) and "en" in culture_codes:
                    return remote_lyrics.value
            language_preference = ContentLanguagePreference.ROMAJI
        if language_preference == ContentLanguagePreference.ROMAJI:
            for remote_lyrics in remote_lyrics_list:
                if remote_lyrics.translation_type == TranslationType.ROMANIZED:
                    return remote_lyrics.value
        if language_preference == ContentLanguagePreference.DEFAULT:
            for remote_lyrics in remote_lyrics_list:
                if remote_lyrics.translation_type == TranslationType.ORIGINAL:
                    return remote_lyrics.value
        return remote_lyrics_list[0].value if remote_lyrics_list else None
