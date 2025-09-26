from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from httpx import QueryParams

from beetsplug.vocadb.vocadb_api_client.api._api_base import ApiBase
from beetsplug.vocadb.vocadb_api_client.models.album_for_api_contract import (
    AlbumForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.album_for_api_contract_partial_find_result import (
    AlbumForApiContractPartialFindResult,
)
from beetsplug.vocadb.vocadb_api_client.models.content_language_preference import (
    ContentLanguagePreference,
)

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Unpack

    from beetsplug.vocadb.vocadb_api_client.models.album_optional_fields import (
        AlbumOptionalFieldsSet,
    )
    from beetsplug.vocadb.vocadb_api_client.models.name_match_mode import (
        NameMatchMode,
    )
    from beetsplug.vocadb.vocadb_api_client.models.song_optional_fields import (
        SongOptionalFieldsSet,
    )


class AlbumApiApi(ApiBase):
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
