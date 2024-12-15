from typing import Any
from unittest import TestCase

from beetsplug.vocadb import VocaDBPlugin


class TestVocaDBPlugin(TestCase):
    def setUp(self):
        self.plugin = VocaDBPlugin()

    def test_get_genres(self):
        info: dict[str, list[dict[str, Any]]] = {}
        self.assertEqual(self.plugin.get_genres(info), "")
        info = {
            "tags": [
                {
                    "count": 0,
                    "tag": {
                        "categoryName": "Genres",
                        "name": "genre1",
                    },
                },
            ]
        }
        self.assertEqual(self.plugin.get_genres(info), "Genre1")
        info = {
            "tags": [
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
            ]
        }
        self.assertEqual(self.plugin.get_genres(info), "Genre1; Genre2")
        info = {
            "tags": [
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
            ]
        }
        self.assertEqual(self.plugin.get_genres(info), "Genre2")

    def test_get_lang(self):
        self.assertEqual(self.plugin.get_lang(["en", "jp"], prefer_romaji=False), "English")
        self.assertEqual(self.plugin.get_lang(["jp", "en"], prefer_romaji=False), "Japanese")
        self.assertEqual(self.plugin.get_lang(["jp", "en"], prefer_romaji=True), "Romaji")
        self.assertEqual(self.plugin.get_lang(["en", "jp"], prefer_romaji=True), "English")
        self.assertEqual(self.plugin.get_lang([], prefer_romaji=True), "English")

    def test_get_lyrics(self):
        lyrics = [
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
        ]
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
        lyrics = [
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
        ]
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "Japanese"), ("Latn", "eng", "lyrics1")
        )
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "English"), ("Latn", "eng", "lyrics2")
        )
        lyrics = [
            {
                "cultureCodes": ["ja"],
                "translationType": "Original",
                "value": "lyrics1",
            },
        ]
        self.assertEqual(
            self.plugin.get_lyrics(lyrics, "English"), ("Jpan", "jpn", "lyrics1")
        )

    def test_get_fallback_lyrics(self):
        lyrics = [
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
        ]
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
        lyrics = [
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
        ]
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "Japanese"),
            "lyrics1",
        )
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "English"),
            "lyrics2",
        )
        lyrics = [
            {
                "cultureCodes": ["ja"],
                "translationType": "Original",
                "value": "lyrics1",
            },
        ]
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "English"),
            "lyrics1",
        )
