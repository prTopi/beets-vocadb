from __future__ import annotations

import sys
from functools import cached_property

import msgspec

from beetsplug.vocadb.vocadb_api_client.models import FrozenBase, StrEnumSet
from beetsplug.vocadb.vocadb_api_client.models.artist_categories import (
    ArtistCategories,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_contract import (
    ArtistContract,
)
from beetsplug.vocadb.vocadb_api_client.models.artist_roles import ArtistRoles

if not sys.version_info < (3, 12):
    from typing import override  # pyright: ignore[reportUnreachable]
else:
    from typing_extensions import override


class ArtistForAlbumForApiContract(
    FrozenBase, dict=True, frozen=True, kw_only=True
):
    _categories: str = msgspec.field(name="categories")
    _effective_roles: str = msgspec.field(name="effectiveRoles")
    is_support: bool
    _roles: str = msgspec.field(name="roles")
    artist: ArtistContract | None = None
    name: str | None = None

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._categories,
                self._effective_roles,
                self.is_support,
                self._roles,
                hash(self.artist) if self.artist else None,
                self.name,
            )
        )

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ArtistForAlbumForApiContract):
            return False
        return (
            self._categories == other._categories
            and self._effective_roles == other._effective_roles
            and self.is_support == other.is_support
            and self._roles == other._roles
            and self.artist == other.artist
            and self.name == other.name
        )

    @cached_property
    def categories(self) -> StrEnumSet[ArtistCategories]:
        return StrEnumSet[ArtistCategories].from_delimited_str(
            ArtistCategories, self._categories
        )

    @cached_property
    def effective_roles(self) -> StrEnumSet[ArtistRoles]:
        return StrEnumSet[ArtistRoles].from_delimited_str(
            ArtistRoles, self._effective_roles
        )

    @cached_property
    def roles(self) -> StrEnumSet[ArtistRoles]:
        return StrEnumSet[ArtistRoles].from_delimited_str(
            ArtistRoles, self._roles
        )
