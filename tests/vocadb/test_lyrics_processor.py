from __future__ import annotations

import sys
from typing import NamedTuple

import msgspec
import pytest

from beetsplug.vocadb.lyrics_processor import LyricsProcessor
from beetsplug.vocadb.vocadb_api_client import (
    ContentLanguagePreference,
    LyricsForSongContract,
)

if not sys.version_info < (3, 12):
    pass  # pyright: ignore[reportUnreachable]
else:
    pass


class LyricsTestCase(NamedTuple):
    lyrics: str
    expected_language_code: str | None
    expected_script: str | None
    language_preference_expected_lyrics_mapping: list[
        tuple[ContentLanguagePreference, str | None]
    ]


class TestLyricsProcessor:
    @pytest.mark.parametrize(
        argnames="test_case",
        argvalues=[
            LyricsTestCase(
                lyrics="""[
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
                expected_language_code="Jpan",
                expected_script="jpn",
                language_preference_expected_lyrics_mapping=[
                    (ContentLanguagePreference.JAPANESE, "lyrics1"),
                    (ContentLanguagePreference.ENGLISH, "lyrics2"),
                    (ContentLanguagePreference.ROMAJI, "lyrics3"),
                    (ContentLanguagePreference.DEFAULT, "lyrics1"),
                ],
            ),
            LyricsTestCase(
                lyrics="""[
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
                expected_language_code="Latn",
                expected_script="eng",
                language_preference_expected_lyrics_mapping=[
                    (ContentLanguagePreference.JAPANESE, "lyrics1"),
                    (ContentLanguagePreference.ENGLISH, "lyrics2"),
                ],
            ),
            LyricsTestCase(
                lyrics="""[
    {
        "cultureCodes": ["ja"],
        "id": 0,
        "translationType": "Original",
        "value": "lyrics1"
    }
]""",
                expected_language_code="Jpan",
                expected_script="jpn",
                language_preference_expected_lyrics_mapping=[
                    (ContentLanguagePreference.ENGLISH, "lyrics1")
                ],
            ),
            LyricsTestCase(
                lyrics="""[
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
                expected_language_code="Jpan",
                expected_script="jpn",
                language_preference_expected_lyrics_mapping=[
                    (ContentLanguagePreference.JAPANESE, "lyrics1"),
                    (ContentLanguagePreference.ENGLISH, "lyrics2"),
                    (ContentLanguagePreference.ROMAJI, "lyrics3"),
                    (ContentLanguagePreference.DEFAULT, "lyrics1"),
                ],
            ),
            LyricsTestCase(
                lyrics="""[
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
                expected_language_code="Latn",
                expected_script="eng",
                language_preference_expected_lyrics_mapping=[
                    (ContentLanguagePreference.JAPANESE, "lyrics1"),
                    (ContentLanguagePreference.ENGLISH, "lyrics2"),
                    (ContentLanguagePreference.DEFAULT, "lyrics2"),
                ],
            ),
            LyricsTestCase(
                lyrics="""[
        {
            "cultureCodes": ["ja"],
            "id": 0,
            "translationType": "Original",
            "value": "lyrics1"
        }
    ]""",
                expected_language_code="Jpan",
                expected_script="jpn",
                language_preference_expected_lyrics_mapping=[
                    (ContentLanguagePreference.DEFAULT, "lyrics1")
                ],
            ),
        ],
    )
    def test_get_lyrics(
        self,
        test_case: LyricsTestCase,
    ) -> None:
        decoded_lyrics: list[LyricsForSongContract] = msgspec.json.decode(
            test_case.lyrics, type=list[LyricsForSongContract]
        )
        expected_language_code: str | None = test_case.expected_language_code
        expected_script: str | None = test_case.expected_script
        language_preference: ContentLanguagePreference
        expected_lyrics: str | None
        for (
            language_preference,
            expected_lyrics,
        ) in test_case.language_preference_expected_lyrics_mapping:
            assert LyricsProcessor(
                language_preference=language_preference
            ).get_lyrics(decoded_lyrics) == (
                expected_language_code,
                expected_script,
                expected_lyrics,
            )
