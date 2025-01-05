from dataclasses import replace
from unittest import TestCase

from dataclass_wizard import fromlist

from beetsplug.vocadb import VocaDBPlugin
from beetsplug.vocadb.api import LyricsFromAPI, TagUsageInResponse


class TestVocaDBPlugin(TestCase):

    plugin: VocaDBPlugin = VocaDBPlugin()

    def __init_subclass__(cls, plugin: VocaDBPlugin) -> None:
        super().__init_subclass__()
        cls.plugin = plugin

    def test_get_genres(self) -> None:
        tags: list[TagUsageInResponse] = []
        self.assertEqual(self.plugin.get_genres(tags), None)
        tags = fromlist(
            TagUsageInResponse,
            [
                {
                    "count": 0,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre1",
                    },
                },
            ],
        )
        self.assertEqual(self.plugin.get_genres(tags), "Genre1")
        tags = fromlist(
            TagUsageInResponse,
            [
                {
                    "count": 2,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre1",
                    },
                },
                {
                    "count": 1,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre2",
                    },
                },
            ],
        )
        self.assertEqual(self.plugin.get_genres(tags), "Genre1; Genre2")
        tags = fromlist(
            TagUsageInResponse,
            [
                {
                    "count": 2,
                    "tag": {
                        "categoryName": "Vocalists",
                        "name": "genre1",
                    },
                },
                {
                    "count": 1,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre2",
                    },
                },
            ],
        )
        self.assertEqual(self.plugin.get_genres(tags), "Genre2")

    def test_get_lang(self) -> None:
        self.plugin.languages = ["en", "jp"]
        self.plugin.instance_config = replace(
            self.plugin.instance_config, prefer_romaji=False
        )
        self.assertEqual(self.plugin.get_lang(), "English")
        self.plugin.languages = ["jp", "en"]
        self.assertEqual(self.plugin.get_lang(), "Japanese")
        self.plugin.instance_config = replace(
            self.plugin.instance_config, prefer_romaji=True
        )
        self.assertEqual(self.plugin.get_lang(), "Romaji")
        self.plugin.languages = ["en", "jp"]
        self.assertEqual(self.plugin.get_lang(), "English")
        self.plugin.languages = []
        self.assertEqual(self.plugin.get_lang(), "English")

    def test_get_lyrics(self) -> None:
        lyrics: list[LyricsFromAPI] = fromlist(
            LyricsFromAPI,
            [
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1",
                },
                {
                    "cultureCodes": ["en"],
                    "id": 123,
                    "source": "FooBar",
                    "translationType": "Translation",
                    "url": "https://foo.bar",
                    "value": "lyrics2",
                },
                {
                    "cultureCodes": [""],
                    "translationType": "Romanized",
                    "value": "lyrics3",
                },
            ],
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "Japanese"), ("Jpan", "jpn", "lyrics1")
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "English"), ("Jpan", "jpn", "lyrics2")
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "Romaji"), ("Jpan", "jpn", "lyrics3")
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, None), ("Jpan", "jpn", "lyrics1")
        )
        lyrics = fromlist(
            LyricsFromAPI,
            [
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Translation",
                    "value": "lyrics1",
                },
                {
                    "cultureCodes": ["en"],
                    "translationType": "Original",
                    "value": "lyrics2",
                },
            ],
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "Japanese"), ("Latn", "eng", "lyrics1")
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "English"), ("Latn", "eng", "lyrics2")
        )
        lyrics = fromlist(
            LyricsFromAPI,
            [
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1",
                },
            ],
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "English"), ("Jpan", "jpn", "lyrics1")
        )

    def test_get_fallback_lyrics(self) -> None:
        lyrics: list[LyricsFromAPI] = fromlist(
            LyricsFromAPI,
            [
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1",
                },
                {
                    "cultureCodes": ["en"],
                    "translationType": "Translation",
                    "value": "lyrics2",
                },
                {
                    "cultureCodes": [""],
                    "translationType": "Romanized",
                    "value": "lyrics3",
                },
            ],
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "Japanese"),
            "lyrics1",
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "English"),
            "lyrics2",
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "Romaji"),
            "lyrics3",
        )
        self.assertEqual(self.plugin.get_fallback_lyrics(lyrics, None), "lyrics1")
        lyrics = fromlist(
            LyricsFromAPI,
            [
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Translation",
                    "value": "lyrics1",
                },
                {
                    "cultureCodes": ["en"],
                    "translationType": "Original",
                    "value": "lyrics2",
                },
            ],
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "Japanese"),
            "lyrics1",
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "English"),
            "lyrics2",
        )
        lyrics = fromlist(
            LyricsFromAPI,
            [
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1",
                },
            ],
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "English"),
            "lyrics1",
        )
