from __future__ import annotations

from . import FrozenBase
from .content_language_selection import ContentLanguageSelection


class LocalizedStringContract(FrozenBase, frozen=True):
    language: ContentLanguageSelection
    value: str | None = None
