from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.tag_for_api_contract import TagForApiContract
from ..models.tag_for_api_contract_partial_find_result import (
    TagForApiContractPartialFindResult,
)
from ._api_base import ApiBase

if TYPE_CHECKING:
    from typing_extensions import Unpack

    from ..models.tag_optional_fields import TagOptionalFields
    from ..models.tag_sort_rule import TagSortRule
    from ._types import ParamsBase, QueryParamsBase


class TagApiApi(ApiBase, path="tags"):
    if TYPE_CHECKING:

        class _ApiTagsGetParams(
            QueryParamsBase[TagOptionalFields, TagSortRule],
            total=False,
        ):
            allowChildren: bool  # noqa: N815
            categoryName: str  # noqa: N815
            target: str
            deleted: bool

    def api_tags_get(
        self, **params: Unpack[_ApiTagsGetParams]
    ) -> TagForApiContractPartialFindResult | None:
        return self.api_client.call_api(
            self.path,
            params=params,
            return_type=TagForApiContractPartialFindResult,
        )

    if TYPE_CHECKING:

        class _ApiTagsIdChildrenGetParams(
            ParamsBase[TagOptionalFields], total=False
        ): ...

    def api_tags_id_children_get(
        self, id_: int, **params: Unpack[_ApiTagsIdChildrenGetParams]
    ) -> tuple[TagForApiContract, ...] | None:
        return self.api_client.call_api(
            self.path,
            str(id_),
            "children",
            params=params,
            return_type=tuple[TagForApiContract, ...],
        )
