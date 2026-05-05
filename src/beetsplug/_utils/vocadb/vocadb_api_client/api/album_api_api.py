from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import httpx

from ..models.album_for_api_contract import AlbumForApiContract
from ..models.album_for_api_contract_partial_find_result import (
    AlbumForApiContractPartialFindResult,
)
from ..models.album_sort_rule import AlbumSortRule
from ..models.disc_type import DiscTypeSet
from ._api_base import ApiBase

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from ..models.album_optional_fields import AlbumOptionalFields
    from ..models.song_optional_fields import SongOptionalFieldsSet
    from ._api_base import AlbumsOrSongsGetParams, ParamsBase


class AlbumApiApi(ApiBase):
    if TYPE_CHECKING:

        class _ApiAlbumsGetParams(
            AlbumsOrSongsGetParams[AlbumOptionalFields, AlbumSortRule],
            total=False,
        ):
            discTypes: DiscTypeSet  # noqa: N815
            barcode: str
            releaseDateAfter: datetime  # noqa: N815
            releaseDateBefore: datetime  # noqa: N815
            deleted: bool

    def api_albums_get(
        self, **params: Unpack[_ApiAlbumsGetParams]
    ) -> AlbumForApiContractPartialFindResult | None:
        return self.api_client.call_api(
            relative_path="albums",
            params=httpx.QueryParams(**params),
            return_type=AlbumForApiContractPartialFindResult,
        )

    if TYPE_CHECKING:

        class _ApiAlbumsIdGetParams(
            ParamsBase[AlbumOptionalFields], total=False
        ):
            songFields: SongOptionalFieldsSet  # noqa: N815

    def api_albums_id_get(
        self, id: int, **params: Unpack[_ApiAlbumsIdGetParams]
    ) -> AlbumForApiContract | None:
        return self.api_client.call_api(
            relative_path=f"albums/{id}",
            params=httpx.QueryParams(**params),
            return_type=AlbumForApiContract,
        )
