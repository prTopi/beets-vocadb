from __future__ import annotations

import posixpath
from typing import TYPE_CHECKING

from ..models.artist_for_api_contract import ArtistForApiContract
from ._api_base import ApiBase

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from ..models.artist_optional_fields import ArtistOptionalFields
    from ..models.artist_relations_fields import ArtistRelationsFieldsSet
    from ._types import ParamsBase


class ArtistApiApi(ApiBase, path="artists"):
    if TYPE_CHECKING:

        class _ApiArtistsIdGetParams(
            ParamsBase[ArtistOptionalFields], total=False
        ):
            relations: ArtistRelationsFieldsSet

    def api_artists_id_get(
        self, id_: int, **params: Unpack[_ApiArtistsIdGetParams]
    ) -> ArtistForApiContract | None:
        return self.api_client.call_api(
            relative_path=posixpath.join(self.path, str(id_)),
            params=params,
            return_type=ArtistForApiContract,
        )
