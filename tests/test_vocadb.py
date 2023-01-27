from unittest import TestCase

from beetsplug.vocadb import VocaDBPlugin


class TestVocaDBPlugin(TestCase):
    def setUp(self):
        self.plugin = VocaDBPlugin()

    def test_get_song_fields(self):
        self.assertEqual(self.plugin.get_song_fields(), "Artists,Tags,Bpm,Lyrics")

    def test_get_lang(self):
        self.assertEqual(self.plugin.get_lang(["en", "jp"]), "English")
        self.assertEqual(self.plugin.get_lang(["jp", "en"]), "Japanese")
        self.plugin.config["prefer_romaji"] = True
        self.assertEqual(self.plugin.get_lang(["jp", "en"]), "Romaji")
        self.assertEqual(self.plugin.get_lang(["en", "jp"]), "English")
        self.assertEqual(self.plugin.get_lang([]), "English")

    def test_get_lyrics(self):
        lyrics = [
            {
                "cultureCode": "ja",
                "translationType": "Original",
                "value": "lyrics1",
            },
            {
                "cultureCode": "en",
                "translationType": "Translation",
                "value": "lyrics2",
            },
            {
                "cultureCode": "",
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
                "cultureCode": "ja",
                "translationType": "Translation",
                "value": "lyrics1",
            },
            {
                "cultureCode": "en",
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
                "cultureCode": "ja",
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
                "cultureCode": "ja",
                "translationType": "Original",
                "value": "lyrics1",
            },
            {
                "cultureCode": "en",
                "translationType": "Translation",
                "value": "lyrics2",
            },
            {
                "cultureCode": "",
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
                "cultureCode": "ja",
                "translationType": "Translation",
                "value": "lyrics1",
            },
            {
                "cultureCode": "en",
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
                "cultureCode": "ja",
                "translationType": "Original",
                "value": "lyrics1",
            },
        ]
        self.assertEqual(
            self.plugin.get_fallback_lyrics(lyrics, "English"),
            "lyrics1",
        )
