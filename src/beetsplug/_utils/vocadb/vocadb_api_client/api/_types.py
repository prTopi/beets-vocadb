from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generic, TypedDict, TypeVar

    from typing_extensions import Required

    from ..models import PascalCaseStrEnum, StrEnumSet
    from ..models.artist_participation_status import ArtistParticipationStatus
    from ..models.content_language_preference import ContentLanguagePreference
    from ..models.entry_status import EntryStatus
    from ..models.name_match_mode import NameMatchMode

    F = TypeVar(name="F", bound=PascalCaseStrEnum)

    class ParamsBase(TypedDict, Generic[F], total=False):
        fields: StrEnumSet[F]
        lang: ContentLanguagePreference

    S = TypeVar(name="S", bound=PascalCaseStrEnum)

    class QueryParamsBase(ParamsBase[F], Generic[F, S], total=False):
        query: Required[str]
        start: int
        maxResults: int
        getTotalCount: bool
        nameMatchMode: NameMatchMode
        sort: S
        status: EntryStatus
        # advancedFilters: list[AdvancedFilters]
        preferAccurateMatches: bool

    class AlbumsOrSongsGetParams(QueryParamsBase[F, S], total=False):
        # TODO: figure out how to handle fields containing brackets
        # tagName[]: list[str]
        # tagId[]: list[ToStr[int]]
        childTags: bool  # noqa: N815
        # artistId[]: list[ToStr[int]]
        artistParticipationStatus: ArtistParticipationStatus  # noqa: N815
        childVoicebanks: bool
        includeMembers: bool
