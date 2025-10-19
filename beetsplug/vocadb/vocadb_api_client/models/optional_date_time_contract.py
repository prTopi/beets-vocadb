from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase


class OptionalDateTimeContract(FrozenBase, frozen=True):
    is_empty: bool
    day: int | None = None
    month: int | None = None
    year: int | None = None
