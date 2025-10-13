from __future__ import annotations

from beetsplug.vocadb.vocadb_api_client.models.artist_for_album_for_api_contract import (  # noqa: E501
    ArtistForAlbumForApiContract,
)


class ArtistForSongContract(ArtistForAlbumForApiContract):
    id: int
    is_custom_name: bool
