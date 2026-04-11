from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import QueryParams

from ..models.album_for_api_contract import AlbumForApiContract
from ..models.album_for_api_contract_partial_find_result import (  # noqa: E501
    AlbumForApiContractPartialFindResult,
)
from ..models.content_language_preference import ContentLanguagePreference
from ._api_base import ApiBase

if TYPE_CHECKING:
    from typing import TypedDict

    from typing_extensions import NotRequired, Unpack

    from ..models.album_optional_fields import AlbumOptionalFieldsSet
    from ..models.name_match_mode import NameMatchMode
    from ..models.song_optional_fields import SongOptionalFieldsSet


class AlbumApiApi(ApiBase):
    if TYPE_CHECKING:

        class _ApiAlbumsGetParams(TypedDict):
            query: str
            maxResults: NotRequired[int]
            nameMatchMode: NotRequired[NameMatchMode]

    def api_albums_get(
        self, **params: Unpack[_ApiAlbumsGetParams]
    ) -> AlbumForApiContractPartialFindResult | None:
        return self.api_client.call_api(
            relative_path="albums",
            params=QueryParams(**params),
            return_type=AlbumForApiContractPartialFindResult,
        )

    if TYPE_CHECKING:

        class _ApiAlbumsIdGetParams(TypedDict):
            lang: NotRequired[ContentLanguagePreference]
            fields: NotRequired[AlbumOptionalFieldsSet]
            songFields: NotRequired[SongOptionalFieldsSet]

    def api_albums_id_get(
        self, id: int, **params: Unpack[_ApiAlbumsIdGetParams]
    ) -> AlbumForApiContract | None:
        return self.api_client.call_api(
            relative_path=f"albums/{id}",
            params=QueryParams(**params),
            return_type=AlbumForApiContract,
        )
