from __future__ import annotations

from ..models import FrozenBase
from .disc_media_type import DiscMediaType


class AlbumDiscPropertiesContract(FrozenBase, frozen=True):
    disc_number: int
    id: int
    media_type: DiscMediaType
    name: str | None = None
