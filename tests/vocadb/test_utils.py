from __future__ import annotations

import msgspec
import pytest

from beetsplug._utils.vocadb.utils import get_genres, get_language_preference
from beetsplug._utils.vocadb.vocadb_api_client import TagUsageForApiContract


@pytest.mark.parametrize(
    argnames="remote_tags, expected",
    argvalues=[
        ("[]", None),
        (
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
            ["Genre1"],
        ),
        (
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
            ["Genre1", "Genre2"],
        ),
        (
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
            ["Genre2"],
        ),
        (
            """[
    {
        "count": 2,
        "tag": {
            "categoryName": "Genres",
            "id": 0,
            "name": "zgenre4"
        }
    },
    {
        "count": 1,
        "tag": {
            "categoryName": "Genres",
            "id": 0,
            "name": "Zgenre5"
        }
    },
    {
        "count": 2,
        "tag": {
            "categoryName": "Genres",
            "id": 0,
            "name": "genre3"
        }
    },
    {
        "count": 2,
        "tag": {
            "categoryName": "Genres",
            "id": 0,
            "name": "agenre1"
        }
    },
    {
        "count": 2,
        "tag": {
            "categoryName": "Genres",
            "id": 0,
            "name": "Agenre2"
        }
    },
    {
        "count": 1,
        "tag": {
            "categoryName": "Genres",
            "id": 0,
            "name": "zgenre6"
        }
    }
]""",
            ["Agenre1", "Agenre2", "Genre3", "Zgenre4", "Zgenre5", "Zgenre6"],
        ),
    ],
)
def test_get_genres(remote_tags: str, expected: list[str] | None) -> None:
    assert (
        get_genres(
            remote_tags=msgspec.json.decode(
                remote_tags, type=tuple[TagUsageForApiContract, ...]
            )
        )
        == expected
    )


@pytest.mark.parametrize(
    argnames="prefer_romaji, languages, expected",
    argvalues=[
        (False, ["en", "jp"], "English"),
        (False, ["jp", "en"], "Japanese"),
        (True, ["jp", "en"], "Romaji"),
        (True, ["en", "jp"], "English"),
        (True, None, "Default"),
    ],
)
def test_get_language_preference(
    prefer_romaji: bool, languages: list[str], expected: str
) -> None:
    assert (
        get_language_preference(
            prefer_romaji=prefer_romaji, languages=languages
        )
        == expected
    )
