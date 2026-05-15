from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.artist_for_api_contract import ArtistForApiContract
from ._api_base import ApiBase

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from typing_extensions import Unpack

    from ..models.artist_optional_fields import ArtistOptionalFields
    from ..models.artist_relations_fields import ArtistRelationsFields
    from ._types import ParamsBase


class ArtistApiApi(ApiBase, path="artists"):
    if TYPE_CHECKING:

        class _ApiArtistsIdGetParams(
            ParamsBase[ArtistOptionalFields], total=False
        ):
            relations: tuple[ArtistRelationsFields, ...]

    def api_artists_id_get(
        self, id_: int | None, **params: Unpack[_ApiArtistsIdGetParams]
    ) -> ArtistForApiContract | None:
        if not id_:
            return None
        return self.api_client.call_api(
            self.path,
            str(id_),
            params=params,
            return_type=ArtistForApiContract,
        )

    def api_artists_ids_get(
        self,
        ids: Iterable[int | None],
        **params: Unpack[_ApiArtistsIdGetParams],
    ) -> Iterator[ArtistForApiContract | None]:
        yield from (
            self.api_client.decode_response(
                response=response, target_type=ArtistForApiContract
            )
            for response in self.api_client.send_requests(
                prepared_requests=[
                    self.api_client.prepare_request(
                        self.path, str(id), params=params
                    )
                    if id
                    else None
                    for id in ids
                ]
            )
        )
