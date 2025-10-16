from unittest import TestCase

import msgspec

from beetsplug.vocadb.utils import get_genres
from beetsplug.vocadb.vocadb_api_client import TagUsageForApiContract


class TestUtils(TestCase):
    def test_get_genres(self) -> None:
        tags: list[TagUsageForApiContract] = []
        assert get_genres(tags) is None
        tags = msgspec.json.decode(
            """[
                {
                    "count": 0,
                    "tag": {
                        "categoryName": "Genres",
                        "id": 0,
                        "name": "genre1"
                    }
                }
            ]""",
            type=list[TagUsageForApiContract],
        )
        assert get_genres(tags) == "Genre1"
        tags = msgspec.json.decode(
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
            type=list[TagUsageForApiContract],
        )
        assert get_genres(tags) == "Genre1; Genre2"
        tags = msgspec.json.decode(
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
            type=list[TagUsageForApiContract],
        )
        assert get_genres(tags) == "Genre2"
