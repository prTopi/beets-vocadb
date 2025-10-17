from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.web_link_category import (
    WebLinkCategory,
)


class WebLinkForApiContract(TaggedBase):
    category: WebLinkCategory
    disabled: bool
    id: int
    description: str | None = None
    url: str | None = None
    description_or_url: str | None = None
