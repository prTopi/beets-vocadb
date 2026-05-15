from __future__ import annotations

from . import PartialFindResult
from .album_for_api_contract import AlbumForApiContract


class AlbumForApiContractPartialFindResult(
    PartialFindResult[AlbumForApiContract], frozen=True
): ...
