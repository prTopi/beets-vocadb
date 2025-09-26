from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.tag_base_contract import (
    TagBaseContract,
)


class TagUsageForApiContract(TaggedBase):
    count: int
    tag: TagBaseContract
