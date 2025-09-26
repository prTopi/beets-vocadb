from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from httpx import QueryParams

from beetsplug.vocadb.vocadb_api_client.api._api_base import ApiBase
from beetsplug.vocadb.vocadb_api_client.models.content_language_preference import (
    ContentLanguagePreference,
)
from beetsplug.vocadb.vocadb_api_client.models.song_for_api_contract import (
    SongForApiContract,
)
from beetsplug.vocadb.vocadb_api_client.models.song_for_api_contract_partial_find_result import (
    SongForApiContractPartialFindResult,
)

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Unpack

    from beetsplug.vocadb.vocadb_api_client.models.name_match_mode import (
        NameMatchMode,
    )
    from beetsplug.vocadb.vocadb_api_client.models.song_optional_fields import (
        SongOptionalFieldsSet,
    )
    from beetsplug.vocadb.vocadb_api_client.models.song_sort_rule import (
        SongSortRule,
    )


class SongApiApi(ApiBase):
    class _ApiSongsGetParams(TypedDict):
        query: str
        maxResults: NotRequired[int]
        sort: NotRequired[SongSortRule]
        preferAccurateMatches: NotRequired[bool]
        nameMatchMode: NotRequired[NameMatchMode]
        fields: NotRequired[SongOptionalFieldsSet]
        lang: NotRequired[ContentLanguagePreference]

    def api_songs_get(
        self,
        **params: Unpack[_ApiSongsGetParams],
    ) -> SongForApiContractPartialFindResult | None:
        return self.api_client.call_api(
            relative_path="songs",
            params=QueryParams(**params),
            return_type=SongForApiContractPartialFindResult,
        )

    class _ApiSongsIdGetParams(TypedDict):
        fields: NotRequired[SongOptionalFieldsSet]
        lang: NotRequired[ContentLanguagePreference]

    def api_songs_id_get(
        self, id: int, **params: Unpack[_ApiSongsIdGetParams]
    ) -> SongForApiContract | None:
        return self.api_client.call_api(
            relative_path=f"songs/{id}",
            params=QueryParams(**params),
            return_type=SongForApiContract,
        )
