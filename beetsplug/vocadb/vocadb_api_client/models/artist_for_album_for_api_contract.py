from __future__ import annotations

from functools import cached_property

import msgspec

from beetsplug.vocadb.vocadb_api_client.models import StrEnumSet, TaggedBase
from beetsplug.vocadb.vocadb_api_client.models.artist_categories import (
    ArtistCategories,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_contract import (
    ArtistContract,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_roles import ArtistRoles


class ArtistForAlbumForApiContract(TaggedBase, dict=True, kw_only=True):
    _categories: str = msgspec.field(name="categories")
    _effective_roles: str = msgspec.field(name="effectiveRoles")
    is_support: bool
    _roles: str = msgspec.field(name="roles")
    artist: ArtistContract | None = None
    name: str | None = None

    @cached_property
    def categories(self) -> StrEnumSet[ArtistCategories]:
        return StrEnumSet[ArtistCategories].from_csv(
            ArtistCategories, self._categories
        )

    @cached_property
    def effective_roles(self) -> StrEnumSet[ArtistRoles]:
        return StrEnumSet[ArtistRoles].from_csv(
            ArtistRoles, self._effective_roles
        )

    @cached_property
    def roles(self) -> StrEnumSet[ArtistRoles]:
        return StrEnumSet[ArtistRoles].from_csv(ArtistRoles, self._roles)
