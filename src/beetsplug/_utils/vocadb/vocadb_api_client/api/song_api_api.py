from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.song_for_api_contract import SongForApiContract
from ..models.song_for_api_contract_partial_find_result import (
    SongForApiContractPartialFindResult,
)
from ._api_base import ApiBase

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from datetime import datetime

    from typing_extensions import Unpack

    from ..models.pv_services import PVServices
    from ..models.song_optional_fields import SongOptionalFields
    from ..models.song_sort_rule import SongSortRule
    from ..models.song_type import SongType
    from ._types import AlbumsOrSongsGetParams, ParamsBase


class SongApiApi(ApiBase, path="songs"):
    if TYPE_CHECKING:

        class _ApiSongsGetParams(
            AlbumsOrSongsGetParams[SongOptionalFields, SongSortRule],
            total=False,
        ):
            songTypes: tuple[SongType, ...]  # noqa: N815
            afterDate: datetime  # noqa: N815
            beforeDate: datetime  # noqa: N815
            unifyTypesAndTags: bool  # noqa: N815
            # artistId[]: tuple[int, ...]
            onlyWithPvs: bool  # noqa: N815
            pvServices: tuple[PVServices, ...]  # noqa: N815
            since: int
            minScore: int  # noqa: N815
            userCollectionId: int  # noqa: N815
            releaseEventId: int  # noqa: N815
            parentSongId: int  # noqa: N815
            minMilliBpm: int  # noqa: N815
            maxMilliBpm: int  # noqa: N815
            minLength: int  # noqa: N815
            maxLength: int  # noqa: N815
            # languages[]: tuple[ContentLanguagePreference, ...]
            # excludedTagIds[]: tuple[int, ...]

    def api_songs_get(
        self,
        **params: Unpack[_ApiSongsGetParams],
    ) -> SongForApiContractPartialFindResult | None:
        return self.api_client.call_api(
            self.path,
            params=params,
            return_type=SongForApiContractPartialFindResult,
        )

    if TYPE_CHECKING:

        class _ApiSongsIdGetParams(
            ParamsBase[SongOptionalFields], total=False
        ): ...

    def api_songs_id_get(
        self, id_: int | None, **params: Unpack[_ApiSongsIdGetParams]
    ) -> SongForApiContract | None:
        if not id_:
            return None
        return self.api_client.call_api(
            self.path,
            str(id_),
            params=params,
            return_type=SongForApiContract,
        )

    def api_songs_ids_get(
        self, ids: Iterable[int | None], **params: Unpack[_ApiSongsIdGetParams]
    ) -> Iterator[SongForApiContract | None]:
        yield from (
            self.api_client.decode_response(
                response=response, target_type=SongForApiContract
            )
            for response in self.api_client.send_requests(
                prepared_requests=[
                    self.api_client.prepare_request(
                        self.path,
                        str(id),
                        params=params,
                    )
                    if id
                    else None
                    for id in ids
                ]
            )
        )
