from __future__ import annotations

import sys
from datetime import datetime
from functools import cached_property

import msgspec

from . import FrozenBase, StrEnumSet
from .entry_status import EntryStatus
from .pv_services import PVServices, PVServicesSet
from .song_type import SongType

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


class SongContract(FrozenBase, frozen=True, dict=True):
    create_date: datetime
    favorited_times: int
    id: int
    length_seconds: int
    _pv_services: str = msgspec.field(name="pvServices")
    rating_score: int
    song_type: SongType
    status: EntryStatus
    version: int
    additional_names: str | None = None
    artist_string: str | None = None
    deleted: bool | None = None
    name: str | None = None
    nico_id: str | None = None
    publish_date: datetime | None = None
    thumb_url: str | None = None

    @override
    def __hash__(self) -> int:
        return hash(self.id)

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SongContract):
            return False
        return self.id == other.id

    @cached_property
    def pv_services(self) -> PVServicesSet:
        return StrEnumSet[PVServices].from_delimited_str(
            PVServices, self._pv_services
        )
