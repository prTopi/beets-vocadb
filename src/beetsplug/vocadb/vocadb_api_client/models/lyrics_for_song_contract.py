from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase
from beetsplug.vocadb.vocadb_api_client.models.translation_type import (
    TranslationType,
)


class LyricsForSongContract(FrozenBase, frozen=True):
    translation_type: TranslationType
    id: int
    value: str | None = None
    culture_codes: set[str] | None = None
    source: str | None = None
    url: str | None = None
