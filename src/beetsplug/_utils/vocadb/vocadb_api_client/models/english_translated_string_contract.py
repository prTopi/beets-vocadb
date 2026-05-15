from __future__ import annotations

from . import FrozenBase


class EnglishTranslatedStringContract(FrozenBase, frozen=True):
    english: str | None = None
    original: str | None = None
