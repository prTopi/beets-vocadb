import abc
from unittest import TestCase

from beetsplug.vocadb.abc import PluginABC
from beetsplug.vocadb.vocadb_api_client import (
    LyricsForSongContract,
    TagUsageForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.content_language_preference import (
    ContentLanguagePreference,
)


class TestABC(TestCase, metaclass=abc.ABCMeta):
    __test__: bool = False
    plugin: PluginABC

    def __init_subclass__(cls, plugin: PluginABC) -> None:
        super().__init_subclass__()
        cls.__test__ = True
        cls.plugin = plugin

    def test_get_genres(self) -> None:
        tags: list[TagUsageForApiContract] = []
        assert self.plugin.get_genres(tags) is None
        tags = self.plugin.album_api.api_client.decode(
            content="""[
                {
                    "count": 0,
                    "tag": {
                        "categoryName": "Genres",
                        "id": 0,
                        "name": "genre1"
                    }
                }
            ]""",
            target_type=list[TagUsageForApiContract],
        )
        assert self.plugin.get_genres(tags) == "Genre1"
        tags = self.plugin.album_api.api_client.decode(
            """[
                {
                    "count": 2,
                    "tag": {
                        "categoryName": "Genres",
                        "id": 0,
                        "name": "genre1"
                    }
                },
                {
                    "count": 1,
                    "tag": {
                        "categoryName": "Genres",
                        "id": 0,
                        "name": "genre2"
                    }
                }
            ]""",
            target_type=list[TagUsageForApiContract],
        )
        assert self.plugin.get_genres(tags) == "Genre1; Genre2"
        tags = self.plugin.album_api.api_client.decode(
            """[
                {
                    "count": 2,
                    "tag": {
                        "categoryName": "Vocalists",
                        "id": 0,
                        "name": "genre1"
                    }
                },
                {
                    "count": 1,
                    "tag": {
                        "categoryName": "Genres",
                        "id": 0,
                        "name": "genre2"
                    }
                }
            ]""",
            target_type=list[TagUsageForApiContract],
        )
        assert self.plugin.get_genres(tags) == "Genre2"

    def test_get_lyrics(self) -> None:
        lyrics: list[LyricsForSongContract] = (
            self.plugin.album_api.api_client.decode(
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
                target_type=list[LyricsForSongContract],
            )
        )
        self.plugin.instance_config.language = (
            ContentLanguagePreference.JAPANESE
        )
        assert self.plugin.get_lyrics(lyrics) == (
            "Jpan",
            "jpn",
            "lyrics1",
        )
        self.plugin.instance_config.language = ContentLanguagePreference.ENGLISH
        assert self.plugin.get_lyrics(lyrics) == (
            "Jpan",
            "jpn",
            "lyrics2",
        )
        self.plugin.instance_config.language = ContentLanguagePreference.ROMAJI
        assert self.plugin.get_lyrics(lyrics) == (
            "Jpan",
            "jpn",
            "lyrics3",
        )
        self.plugin.instance_config.language = ContentLanguagePreference.DEFAULT
        assert self.plugin.get_lyrics(lyrics) == (
            "Jpan",
            "jpn",
            "lyrics1",
        )
        lyrics = self.plugin.album_api.api_client.decode(
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
            target_type=list[LyricsForSongContract],
        )
        self.plugin.instance_config.language = (
            ContentLanguagePreference.JAPANESE
        )
        assert self.plugin.get_lyrics(lyrics) == (
            "Latn",
            "eng",
            "lyrics1",
        )
        self.plugin.instance_config.language = ContentLanguagePreference.ENGLISH
        assert self.plugin.get_lyrics(lyrics) == (
            "Latn",
            "eng",
            "lyrics2",
        )
        lyrics = self.plugin.album_api.api_client.decode(
            """[
                {
                    "cultureCodes": ["ja"],
                    "id": 0,
                    "translationType": "Original",
                    "value": "lyrics1"
                }
            ]""",
            target_type=list[LyricsForSongContract],
        )
        assert self.plugin.get_lyrics(lyrics) == (
            "Jpan",
            "jpn",
            "lyrics1",
        )

    def test_get_fallback_lyrics(self) -> None:
        lyrics: list[LyricsForSongContract] = (
            self.plugin.album_api.api_client.decode(
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
                target_type=list[LyricsForSongContract],
            )
        )
        self.plugin.instance_config.language = (
            ContentLanguagePreference.JAPANESE
        )
        assert self.plugin.get_fallback_lyrics(lyrics) == "lyrics1"
        self.plugin.instance_config.language = ContentLanguagePreference.ENGLISH
        assert self.plugin.get_fallback_lyrics(lyrics) == "lyrics2"
        self.plugin.instance_config.language = ContentLanguagePreference.ROMAJI
        assert self.plugin.get_fallback_lyrics(lyrics) == "lyrics3"
        self.plugin.instance_config.language = ContentLanguagePreference.DEFAULT
        assert self.plugin.get_fallback_lyrics(lyrics) == "lyrics1"
        lyrics = self.plugin.album_api.api_client.decode(
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
            target_type=list[LyricsForSongContract],
        )
        self.plugin.instance_config.language = (
            ContentLanguagePreference.JAPANESE
        )
        assert self.plugin.get_fallback_lyrics(lyrics) == "lyrics1"
        self.plugin.instance_config.language = ContentLanguagePreference.ENGLISH
        assert self.plugin.get_fallback_lyrics(lyrics) == "lyrics2"
        self.plugin.instance_config.language = ContentLanguagePreference.DEFAULT
        assert self.plugin.get_fallback_lyrics(lyrics) == "lyrics2"
        lyrics = self.plugin.album_api.api_client.decode(
            """[
                {
                    "cultureCodes": ["ja"],
                    "id": 0,
                    "translationType": "Original",
                    "value": "lyrics1"
                }
            ]""",
            target_type=list[LyricsForSongContract],
        )
        assert self.plugin.get_fallback_lyrics(lyrics) == "lyrics1"
