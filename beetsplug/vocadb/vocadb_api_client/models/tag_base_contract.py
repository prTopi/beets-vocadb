from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase


class TagBaseContract(TaggedBase):
    id: int
    name: str | None = None
    additional_names: str | None = None
    category_name: str | None = None
    url_slug: str | None = None
