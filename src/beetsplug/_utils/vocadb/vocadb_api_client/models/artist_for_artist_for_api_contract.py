from __future__ import annotations

from . import FrozenBase
from .artist_contract import ArtistContract
from .artist_link_type import ArtistLinkType


class ArtistForArtistForApiContract(FrozenBase, frozen=True):
    artist: ArtistContract
    link_type: ArtistLinkType
