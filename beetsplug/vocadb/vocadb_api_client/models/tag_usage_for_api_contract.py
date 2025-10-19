from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase
from beetsplug.vocadb.vocadb_api_client.models.tag_base_contract import (
    TagBaseContract,
)


class TagUsageForApiContract(FrozenBase, frozen=True):
    count: int
    tag: TagBaseContract
