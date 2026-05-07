from __future__ import annotations

from . import FrozenBase
from .song_for_api_contract import SongForApiContract


class SongInAlbumForApiContract(FrozenBase, frozen=True):
    disc_number: int
    id: int
    track_number: int
    # rating: SongVoteRating | None = None
    song: SongForApiContract | None = None
    computed_culture_codes: tuple[str, ...] | None = None
    name: str | None = None
