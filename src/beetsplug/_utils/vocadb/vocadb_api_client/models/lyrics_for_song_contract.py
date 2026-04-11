from __future__ import annotations

from . import FrozenBase
from .translation_type import TranslationType


class LyricsForSongContract(FrozenBase, frozen=True):
    translation_type: TranslationType
    id: int
    value: str | None = None
    culture_codes: set[str] | None = None
    source: str | None = None
    url: str | None = None
