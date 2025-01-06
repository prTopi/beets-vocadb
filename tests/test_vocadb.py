from unittest import TestCase

from cattrs import structure

from beetsplug.vocadb import VocaDBPlugin
from beetsplug.vocadb.requests_handler.models import Lyrics, TagUsage


class TestVocaDBPlugin(TestCase):

    plugin: VocaDBPlugin = VocaDBPlugin()

    def __init_subclass__(cls, plugin: VocaDBPlugin) -> None:
        super().__init_subclass__()
        cls.plugin = plugin

    def test_get_genres(self) -> None:
        tags: list[TagUsage] = []
        self.assertEqual(self.plugin.get_genres(tags), None)
        tags = structure(
            [
                {
                    "count": 0,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre1",
                    },
                },
            ],
            list[TagUsage],
        )
        self.assertEqual(self.plugin.get_genres(tags), "Genre1")
        tags = structure(
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
            list[TagUsage],
        )
        self.assertEqual(self.plugin.get_genres(tags), "Genre1; Genre2")
        tags = structure(
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
            list[TagUsage],
        )
        self.assertEqual(self.plugin.get_genres(tags), "Genre2")

    def test_get_lang(self) -> None:
        self.plugin.languages = ["en", "jp"]
        self.plugin.instance_config.prefer_romaji = False
        self.assertEqual(self.plugin.get_lang(), "English")
        self.plugin.languages = ["jp", "en"]
        self.assertEqual(self.plugin.get_lang(), "Japanese")
        self.plugin.instance_config.prefer_romaji = True
        self.assertEqual(self.plugin.get_lang(), "Romaji")
        self.plugin.languages = ["en", "jp"]
        self.assertEqual(self.plugin.get_lang(), "English")
        self.plugin.languages = []
        self.assertEqual(self.plugin.get_lang(), "English")

    def test_get_lyrics(self) -> None:
        lyrics: list[Lyrics] = structure(
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
            list[Lyrics],
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
        lyrics = structure(
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
            list[Lyrics],
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "Japanese"), ("Latn", "eng", "lyrics1")
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "English"), ("Latn", "eng", "lyrics2")
        )
        lyrics = structure(
            [
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1",
                },
            ],
            list[Lyrics],
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "English"), ("Jpan", "jpn", "lyrics1")
        )

    def test_get_fallback_lyrics(self) -> None:
        lyrics: list[Lyrics] = structure(
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
            list[Lyrics],
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
        lyrics = structure(
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
            list[Lyrics],
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "Japanese"),
            "lyrics1",
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "English"),
            "lyrics2",
        )
        lyrics = structure(
            [
                {
                    "cultureCodes": ["ja"],
                    "translationType": "Original",
                    "value": "lyrics1",
                },
            ],
            list[Lyrics],
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "English"),
            "lyrics1",
        )
