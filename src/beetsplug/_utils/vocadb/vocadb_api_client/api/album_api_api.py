from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.album_for_api_contract import AlbumForApiContract
from ..models.album_for_api_contract_partial_find_result import (
    AlbumForApiContractPartialFindResult,
)
from ._api_base import ApiBase

if TYPE_CHECKING:
    from datetime import datetime

    from typing_extensions import Unpack

    from ..models.album_optional_fields import AlbumOptionalFields
    from ..models.album_sort_rule import AlbumSortRule
    from ..models.disc_type import DiscType
    from ..models.song_optional_fields import SongOptionalFields
    from ._types import AlbumsOrSongsGetParams, ParamsBase


class AlbumApiApi(ApiBase, path="albums"):
    if TYPE_CHECKING:

        class _ApiAlbumsGetParams(
            AlbumsOrSongsGetParams[AlbumOptionalFields, AlbumSortRule],
            total=False,
            closed=True,
        ):
            discTypes: tuple[DiscType, ...]  # noqa: N815
            barcode: str
            releaseDateAfter: datetime  # noqa: N815
            releaseDateBefore: datetime  # noqa: N815
            deleted: bool

    def api_albums_get(
        self, **params: Unpack[_ApiAlbumsGetParams]
    ) -> AlbumForApiContractPartialFindResult | None:
        return self.api_client.call_api(
            self.path,
            params=params,
            return_type=AlbumForApiContractPartialFindResult,
        )

    if TYPE_CHECKING:

        class _ApiAlbumsIdGetParams(
            ParamsBase[AlbumOptionalFields], total=False
        ):
            songFields: tuple[SongOptionalFields, ...]  # noqa: N815

    def api_albums_id_get(
        self, id_: int, **params: Unpack[_ApiAlbumsIdGetParams]
    ) -> AlbumForApiContract | None:
        return self.api_client.call_api(
            self.path,
            str(id_),
            params=params,
            return_type=AlbumForApiContract,
        )
