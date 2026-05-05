from __future__ import annotations

from . import FrozenBase


class TagBaseContract(FrozenBase, frozen=True):
    id: int
    additional_names: str | None = None
    category_name: str | None = None
    name: str | None = None
    url_slug: str | None = None
