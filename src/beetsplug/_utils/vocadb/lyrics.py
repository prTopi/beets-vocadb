from __future__ import annotations

from typing import TYPE_CHECKING

from .vocadb_api_client import ContentLanguagePreference, TranslationType

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import TypedDict

    from .vocadb_api_client import LyricsForSongContract

    class LyricsInfo(TypedDict, closed=True):
        script: str | None
        language: str | None
        lyrics: str | None


class LyricsProcessor:
    def __init__(self, language_preference: str) -> None:
        self.language_preference: str = language_preference

    def get_lyrics(
        self,
        remote_lyrics: Iterable[LyricsForSongContract] | None,
    ) -> LyricsInfo:
        """Extract lyrics information with language and script metadata.

        Processes available lyrics versions to select the most appropriate one
        based on user language preferences and translation type. Also determines
        the script system and language code for the selected lyrics.
        """
        script: str | None = None
        language: str | None = None
        lyrics: str | None = None

        remote_lyrics_item: LyricsForSongContract
        for remote_lyrics_item in remote_lyrics or ():
            remote_translation_type: TranslationType = (
                remote_lyrics_item.translation_type
            )
            value: str | None = remote_lyrics_item.value
            # get the intersection
            culture_codes: set[str] | None = {
                "en",
                "ja",
            } & set(
                remote_culture_codes
                if (remote_culture_codes := remote_lyrics_item.culture_codes)
                else ()
            )

            if not culture_codes:
                if (
                    self.language_preference == ContentLanguagePreference.ROMAJI
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

        if not lyrics and remote_lyrics:
            lyrics = self._get_fallback_lyrics(
                remote_lyrics,
            )

        return {"script": script, "language": language, "lyrics": lyrics}

    def _get_fallback_lyrics(
        self,
        remote_lyrics: Iterable[LyricsForSongContract],
    ) -> str | None:
        """Internal fallback mechanism when preferred lyrics are not available.

        Implements a fallback strategy for lyrics selection when the user's
        preferred language/translation type combination is not available.
        Falls back through English, Romanized, and finally Original lyrics.
        """
        if not remote_lyrics:
            return None

        preference_to_translation_type: dict[
            ContentLanguagePreference, TranslationType
        ] = {
            ContentLanguagePreference.ENGLISH: TranslationType.ORIGINAL,
            ContentLanguagePreference.ROMAJI: TranslationType.ROMANIZED,
            ContentLanguagePreference.DEFAULT: TranslationType.ORIGINAL,
        }

        preference: ContentLanguagePreference
        for preference in [
            ContentLanguagePreference(value=self.language_preference),
            ContentLanguagePreference.ROMAJI,
            ContentLanguagePreference.DEFAULT,
        ]:
            translation_type: TranslationType | None
            if (
                translation_type := (
                    preference_to_translation_type.get(preference)
                )
            ) is None:
                continue

            for item in remote_lyrics:
                if item.translation_type == translation_type:
                    if preference == ContentLanguagePreference.ENGLISH:
                        if item.culture_codes and "en" in item.culture_codes:
                            return item.value
                    else:
                        return item.value

        return next(iter(remote_lyrics)).value
