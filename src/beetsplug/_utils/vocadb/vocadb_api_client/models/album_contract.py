from __future__ import annotations

from datetime import datetime

from . import FrozenBase
from .disc_type import DiscType
from .entry_status import EntryStatus
from .optional_date_time_contract import OptionalDateTimeContract


class AlbumContract(FrozenBase, frozen=True):
    create_date: datetime
    disc_type: DiscType
    id: int
    rating_average: float
    rating_count: int
    release_date: OptionalDateTimeContract
    # release_event: ReleaseEventForApiContract | None = None
    status: EntryStatus
    version: int
    additional_names: str | None = None
    artist_string: str | None = None
    cover_picture_mime: str | None = None
    deleted: bool | None = None
    name: str | None = None
