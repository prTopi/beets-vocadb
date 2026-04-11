from __future__ import annotations

from . import FrozenBase
from .tag_base_contract import TagBaseContract


class TagUsageForApiContract(FrozenBase, frozen=True):
    count: int
    tag: TagBaseContract
