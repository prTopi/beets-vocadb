import sys
from unittest import TestCase

import msgspec

from beetsplug.vocadb.lyrics_processor import LyricsProcessor
from beetsplug.vocadb.vocadb_api_client import (
    ContentLanguagePreference,
    LyricsForSongContract,
)

if not sys.version_info < (3, 12):
    pass  # pyright: ignore[reportUnreachable]
else:
    pass


class TestLyricsProcessor(TestCase):
    lyrics_processors: dict[ContentLanguagePreference, LyricsProcessor] = {
        language_preference: LyricsProcessor(
            language_preference=language_preference
        )
        for language_preference in ContentLanguagePreference
    }

    def test_get_lyrics(self) -> None:
        lyrics: list[LyricsForSongContract] = msgspec.json.decode(
            """[
                {
                    "cultureCodes": ["ja"],
                    "id": 0,
                    "translationType": "Original",
                    "value": "lyrics1"
                },
                {
                    "cultureCodes": ["en"],
                    "id": 0,
                    "source": "FooBar",
                    "translationType": "Translation",
                    "url": "https://foo.bar",
                    "value": "lyrics2"
                },
                {
                    "cultureCodes": [""],
                    "id": 0,
                    "translationType": "Romanized",
                    "value": "lyrics3"
                }
            ]""",
            type=list[LyricsForSongContract],
        )
        assert self.lyrics_processors[
            ContentLanguagePreference.JAPANESE
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics1")
        assert self.lyrics_processors[
            ContentLanguagePreference.ENGLISH
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics2")
        assert self.lyrics_processors[
            ContentLanguagePreference.ROMAJI
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics3")
        assert self.lyrics_processors[
            ContentLanguagePreference.DEFAULT
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics1")
        lyrics = msgspec.json.decode(
            """[
                {
                    "cultureCodes": ["ja"],
                    "id": 0,
                    "translationType": "Translation",
                    "value": "lyrics1"
                },
                {
                    "cultureCodes": ["en"],
                    "id": 0,
                    "translationType": "Original",
                    "value": "lyrics2"
                }
            ]""",
            type=list[LyricsForSongContract],
        )
        assert self.lyrics_processors[
            ContentLanguagePreference.JAPANESE
        ].get_lyrics(lyrics) == ("Latn", "eng", "lyrics1")
        assert self.lyrics_processors[
            ContentLanguagePreference.ENGLISH
        ].get_lyrics(lyrics) == ("Latn", "eng", "lyrics2")
        lyrics = msgspec.json.decode(
            """[
                {
                    "cultureCodes": ["ja"],
                    "id": 0,
                    "translationType": "Original",
                    "value": "lyrics1"
                }
            ]""",
            type=list[LyricsForSongContract],
        )
        assert self.lyrics_processors[
            ContentLanguagePreference.ENGLISH
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics1")

        lyrics = msgspec.json.decode(
            """[
                {
                    "cultureCodes": ["ja"],
                    "id": 0,
                    "translationType": "Original",
                    "value": "lyrics1"
                },
                {
                    "cultureCodes": ["en"],
                    "id": 0,
                    "translationType": "Translation",
                    "value": "lyrics2"
                },
                {
                    "cultureCodes": [""],
                    "id": 0,
                    "translationType": "Romanized",
                    "value": "lyrics3"
                }
            ]""",
            type=list[LyricsForSongContract],
        )
        assert self.lyrics_processors[
            ContentLanguagePreference.JAPANESE
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics1")
        assert self.lyrics_processors[
            ContentLanguagePreference.ENGLISH
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics2")
        assert self.lyrics_processors[
            ContentLanguagePreference.ROMAJI
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics3")
        assert self.lyrics_processors[
            ContentLanguagePreference.DEFAULT
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics1")
        lyrics = msgspec.json.decode(
            """[
                {
                    "cultureCodes": ["ja"],
                    "id": 0,
                    "translationType": "Translation",
                    "value": "lyrics1"
                },
                {
                    "cultureCodes": ["en"],
                    "id": 0,
                    "translationType": "Original",
                    "value": "lyrics2"
                }
            ]""",
            type=list[LyricsForSongContract],
        )
        assert self.lyrics_processors[
            ContentLanguagePreference.JAPANESE
        ].get_lyrics(lyrics) == ("Latn", "eng", "lyrics1")
        assert self.lyrics_processors[
            ContentLanguagePreference.ENGLISH
        ].get_lyrics(lyrics) == ("Latn", "eng", "lyrics2")
        assert self.lyrics_processors[
            ContentLanguagePreference.DEFAULT
        ].get_lyrics(lyrics) == ("Latn", "eng", "lyrics2")
        lyrics = msgspec.json.decode(
            """[
                {
                    "cultureCodes": ["ja"],
                    "id": 0,
                    "translationType": "Original",
                    "value": "lyrics1"
                }
            ]""",
            type=list[LyricsForSongContract],
        )
        assert self.lyrics_processors[
            ContentLanguagePreference.DEFAULT
        ].get_lyrics(lyrics) == ("Jpan", "jpn", "lyrics1")
