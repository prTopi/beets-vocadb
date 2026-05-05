from __future__ import annotations

from . import PartialFindResult
from .tag_for_api_contract import TagForApiContract


class TagForApiContractPartialFindResult(
    PartialFindResult[TagForApiContract], frozen=True
): ...
