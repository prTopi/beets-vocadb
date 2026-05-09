from __future__ import annotations

import posixpath
from typing import TYPE_CHECKING

from ..models.song_for_api_contract import SongForApiContract
from ..models.song_for_api_contract_partial_find_result import (
    SongForApiContractPartialFindResult,
)
from ._api_base import ApiBase

if TYPE_CHECKING:
    from datetime import datetime

    from typing_extensions import Unpack

    from ..models.pv_services import PVServicesSet
    from ..models.song_optional_fields import SongOptionalFields
    from ..models.song_sort_rule import SongSortRule
    from ..models.song_type import SongTypeSet
    from ._types import AlbumsOrSongsGetParams, ParamsBase


class SongApiApi(ApiBase, path="songs"):
    if TYPE_CHECKING:

        class _ApiSongsGetParams(
            AlbumsOrSongsGetParams[SongOptionalFields, SongSortRule],
            total=False,
        ):
            songTypes: SongTypeSet  # noqa: N815
            afterDate: datetime  # noqa: N815
            beforeDate: datetime  # noqa: N815
            unifyTypesAndTags: bool  # noqa: N815
            # artistId[]: Iterable[int]
            onlyWithPvs: bool  # noqa: N815
            pvServices: PVServicesSet  # noqa: N815
            since: int
            minScore: int  # noqa: N815
            userCollectionId: int  # noqa: N815
            releaseEventId: int  # noqa: N815
            parentSongId: int  # noqa: N815
            minMilliBpm: int  # noqa: N815
            maxMilliBpm: int  # noqa: N815
            minLength: int  # noqa: N815
            maxLength: int  # noqa: N815
            # languages[]: Iterable[ContentLanguagePreference]
            # excludedTagIds[]: Iterable[int]

    def api_songs_get(
        self,
        **params: Unpack[_ApiSongsGetParams],
    ) -> SongForApiContractPartialFindResult | None:
        return self.api_client.call_api(
            relative_path=self.path,
            params=params,  # pyrefly: ignore[bad-argument-type]
            return_type=SongForApiContractPartialFindResult,
        )

    if TYPE_CHECKING:

        class _ApiSongsIdGetParams(
            ParamsBase[SongOptionalFields], total=False
        ): ...

    def api_songs_id_get(
        self, id: int, **params: Unpack[_ApiSongsIdGetParams]
    ) -> SongForApiContract | None:
        return self.api_client.call_api(
            relative_path=posixpath.join(self.path, str(id)),
            params=params,  # pyrefly: ignore[bad-argument-type]
            return_type=SongForApiContract,
        )
