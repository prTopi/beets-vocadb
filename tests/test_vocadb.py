from unittest import TestCase

import msgspec

from beetsplug.vocadb import VocaDBPlugin
from beetsplug.vocadb.requests_handler.models import Lyrics, TagUsage


class TestVocaDBPlugin(TestCase):
    plugin: VocaDBPlugin = VocaDBPlugin()

    def __init_subclass__(cls, plugin: VocaDBPlugin) -> None:
        super().__init_subclass__()
        cls.plugin = plugin

    def test_get_genres(self) -> None:
        tags: list[TagUsage] = []
        assert self.plugin.get_genres(tags) is None
        tags = msgspec.json.decode(
            b"""[
                {
                    "count": 0,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre1"
                    }
                }
            ]""",
            type=list[TagUsage],
        )
        assert self.plugin.get_genres(tags) == "Genre1"
        tags = msgspec.json.decode(
            b"""[
                {
                    "count": 2,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre1"
                    }
                },
                {
                    "count": 1,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre2"
                    }
                }
            ]""",
            type=list[TagUsage],
        )
        assert self.plugin.get_genres(tags) == "Genre1; Genre2"
        tags = msgspec.json.decode(
            b"""[
                {
                    "count": 2,
                    "tag": {
                        "categoryName": "Vocalists",
                        "name": "genre1"
                    }
                },
                {
                    "count": 1,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre2"
                    }
                }
            ]""",
            type=list[TagUsage],
        )
        assert self.plugin.get_genres(tags) == "Genre2"

    def test_get_lang(self) -> None:
        self.plugin.languages = ["en", "jp"]
        self.plugin.instance_config.prefer_romaji = False
        assert self.plugin.get_lang() == "English"
        self.plugin.languages = ["jp", "en"]
        assert self.plugin.get_lang() == "Japanese"
        self.plugin.instance_config.prefer_romaji = True
        assert self.plugin.get_lang() == "Romaji"
        self.plugin.languages = ["en", "jp"]
        assert self.plugin.get_lang() == "English"
        self.plugin.languages = []
        assert self.plugin.get_lang() == "English"

    def test_get_lyrics(self) -> None:
        lyrics: list[Lyrics] = msgspec.json.decode(
            b"""[
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1"
                },
                {
                    "cultureCodes": ["en"],
                    "id": 123,
                    "source": "FooBar",
                    "translationType": "Translation",
                    "url": "https://foo.bar",
                    "value": "lyrics2"
                },
                {
                    "cultureCodes": [""],
                    "translationType": "Romanized",
                    "value": "lyrics3"
                }
            ]""",
            type=list[Lyrics],
        )
        assert self.plugin.get_lyrics(lyrics, "Japanese") == (
            "Jpan",
            "jpn",
            "lyrics1",
        )
        assert self.plugin.get_lyrics(lyrics, "English") == (
            "Jpan",
            "jpn",
            "lyrics2",
        )
        assert self.plugin.get_lyrics(lyrics, "Romaji") == (
            "Jpan",
            "jpn",
            "lyrics3",
        )
        assert self.plugin.get_lyrics(lyrics, None) == (
            "Jpan",
            "jpn",
            "lyrics1",
        )
        lyrics = msgspec.json.decode(
            b"""[
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Translation",
                    "value": "lyrics1"
                },
                {
                    "cultureCodes": ["en"],
                    "translationType": "Original",
                    "value": "lyrics2"
                }
            ]""",
            type=list[Lyrics],
        )
        assert self.plugin.get_lyrics(lyrics, "Japanese") == (
            "Latn",
            "eng",
            "lyrics1",
        )
        assert self.plugin.get_lyrics(lyrics, "English") == (
            "Latn",
            "eng",
            "lyrics2",
        )
        lyrics = msgspec.json.decode(
            b"""[
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1"
                }
            ]""",
            type=list[Lyrics],
        )
        assert self.plugin.get_lyrics(lyrics, "English") == (
            "Jpan",
            "jpn",
            "lyrics1",
        )

    def test_get_fallback_lyrics(self) -> None:
        lyrics: list[Lyrics] = msgspec.json.decode(
            b"""[
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1"
                },
                {
                    "cultureCodes": ["en"],
                    "translationType": "Translation",
                    "value": "lyrics2"
                },
                {
                    "cultureCodes": [""],
                    "translationType": "Romanized",
                    "value": "lyrics3"
                }
            ]""",
            type=list[Lyrics],
        )
        assert self.plugin.get_fallback_lyrics(lyrics, "Japanese") == "lyrics1"
        assert self.plugin.get_fallback_lyrics(lyrics, "English") == "lyrics2"
        assert self.plugin.get_fallback_lyrics(lyrics, "Romaji") == "lyrics3"
        assert self.plugin.get_fallback_lyrics(lyrics, None) == "lyrics1"
        lyrics = msgspec.json.decode(
            b"""[
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Translation",
                    "value": "lyrics1"
                },
                {
                    "cultureCodes": ["en"],
                    "translationType": "Original",
                    "value": "lyrics2"
                }
            ]""",
            type=list[Lyrics],
        )
        assert self.plugin.get_fallback_lyrics(lyrics, "Japanese") == "lyrics1"
        assert self.plugin.get_fallback_lyrics(lyrics, "English") == "lyrics2"
        lyrics = msgspec.json.decode(
            b"""[
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1"
                }
            ]""",
            type=list[Lyrics],
        )
        assert self.plugin.get_fallback_lyrics(lyrics, "English") == "lyrics1"
