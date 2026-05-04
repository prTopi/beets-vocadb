from __future__ import annotations

from . import PartialFindResult
from .song_for_api_contract import SongForApiContract


class SongForApiContractPartialFindResult(
    PartialFindResult[SongForApiContract], frozen=True
): ...
