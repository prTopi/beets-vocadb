from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase


class OptionalDateTimeContract(TaggedBase):
    is_empty: bool
    day: int | None = None
    month: int | None = None
    year: int | None = None
