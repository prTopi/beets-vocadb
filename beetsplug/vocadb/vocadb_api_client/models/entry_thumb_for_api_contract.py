from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase


class EntryThumbForApiContract(FrozenBase, frozen=True):
    mime: str | None = None
    name: str | None = None
    url_original: str | None = None
    url_small_thumb: str | None = None
    url_thumb: str | None = None
    url_tiny_thumb: str | None = None
