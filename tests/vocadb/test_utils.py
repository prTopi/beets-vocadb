from __future__ import annotations

import msgspec
import pytest

from beetsplug.vocadb.utils import get_genres
from beetsplug.vocadb.vocadb_api_client import TagUsageForApiContract


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
            "Genre1",
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
            "Genre1; Genre2",
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
            "Genre2",
        ),
    ],
)
def test_get_genres(remote_tags: str, expected: str | None) -> None:
    assert (
        get_genres(
            remote_tags=msgspec.json.decode(
                remote_tags, type=tuple[TagUsageForApiContract, ...]
            )
        )
        == expected
    )
