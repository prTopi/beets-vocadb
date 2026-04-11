from __future__ import annotations

from .artist_for_album_for_api_contract import ArtistForAlbumForApiContract


class ArtistForSongContract(ArtistForAlbumForApiContract, frozen=True):
    id: int
    is_custom_name: bool
