from unittest import TestCase

from beetsplug.vocadb import LyricsDict, TagUsageDict, VocaDBPlugin


class TestVocaDBPlugin(TestCase):

    plugin: VocaDBPlugin = VocaDBPlugin()

    def __init_subclass__(cls, plugin: VocaDBPlugin) -> None:
        super().__init_subclass__()
        cls.plugin = plugin

    def test_get_genres(self) -> None:
        tags: list[TagUsageDict] = []
        self.assertEqual(self.plugin.get_genres(tags), None)
        tags = [
            {
                "count": 0,
                "tag": {
                    "categoryName": "Genres",
                    "name": "genre1",
                },
            },
        ]
        self.assertEqual(self.plugin.get_genres(tags), "Genre1")
        tags = [
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
        self.assertEqual(self.plugin.get_genres(tags), "Genre1; Genre2")
        tags = [
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
        self.assertEqual(self.plugin.get_genres(tags), "Genre2")

    def test_language(self) -> None:
        self.plugin.languages = ["en", "jp"]
        self.plugin.config["prefer_romaji"] = False
        self.assertEqual(self.plugin.language, "English")
        self.plugin.languages = ["jp", "en"]
        self.assertEqual(self.plugin.language, "Japanese")
        self.plugin.config["prefer_romaji"] = True
        self.assertEqual(self.plugin.language, "Romaji")
        self.plugin.languages = ["en", "jp"]
        self.assertEqual(self.plugin.language, "English")
        self.plugin.languages = []
        self.assertEqual(self.plugin.language, "English")

    def test_get_lyrics(self) -> None:
        lyrics: list[LyricsDict] = [
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

    def test_get_fallback_lyrics(self) -> None:
        lyrics: list[LyricsDict] = [
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
