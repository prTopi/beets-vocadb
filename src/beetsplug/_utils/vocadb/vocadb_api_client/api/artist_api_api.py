from __future__ import annotations

from typing import TYPE_CHECKING

from httpx import QueryParams

from ..models.artist_for_api_contract import ArtistForApiContract
from ..models.artist_optional_fields import ArtistOptionalFields
from ..models.artist_relations_fields import ArtistRelationsFieldsSet
from ._api_base import ApiBase

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from ._api_base import ParamsBase


class ArtistApiApi(ApiBase):
    if TYPE_CHECKING:

        class _ApiArtistsIdGetParams(
            ParamsBase[ArtistOptionalFields], total=False
        ):
            relations: ArtistRelationsFieldsSet

    def api_artists_id_get(
        self, id: int, **params: Unpack[_ApiArtistsIdGetParams]
    ) -> ArtistForApiContract | None:
        return self.api_client.call_api(
            relative_path=f"artists/{id}",
            params=QueryParams(**params),
            return_type=ArtistForApiContract,
        )
