from __future__ import annotations

from datetime import datetime

from . import FrozenBase
from .artist_type import ArtistType
from .entry_status import EntryStatus


class ArtistContract(FrozenBase, frozen=True):
    artist_type: ArtistType
    id: int
    status: EntryStatus
    version: int
    additional_names: str | None = None
    deleted: bool | None = None
    name: str | None = None
    release_date: datetime | None = None
    picture_mime: str | None = None
