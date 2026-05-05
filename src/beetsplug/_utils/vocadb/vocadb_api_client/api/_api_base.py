from typing import TYPE_CHECKING, Generic, TypedDict, TypeVar

from typing_extensions import Required

from ..api_client import ApiClient
from ..models import PascalCaseStrEnum, StrEnumSet
from ..models.artist_participation_status import ArtistParticipationStatus
from ..models.content_language_preference import ContentLanguagePreference
from ..models.entry_status import EntryStatus
from ..models.name_match_mode import NameMatchMode


class ApiBase:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client: ApiClient = api_client


if TYPE_CHECKING:
    F = TypeVar("F", bound=PascalCaseStrEnum)

    class ParamsBase(TypedDict, Generic[F], total=False):
        fields: StrEnumSet[F]
        lang: ContentLanguagePreference

    S = TypeVar("S", bound=PascalCaseStrEnum)

    class QueryParamsBase(ParamsBase[F], Generic[F, S], total=False):
        query: Required[str]
        start: int
        maxResults: int
        getTotalCount: bool
        nameMatchMode: NameMatchMode
        sort: S
        status: EntryStatus
        # advancedFilters: Iterable[AdvancedFilters]
        preferAccurateMatches: bool

    class AlbumsOrSongsGetParams(QueryParamsBase[F, S], total=False):
        # TODO: figure out how to handle fields containing brackets
        # tagName[]: Iterable[str]
        # tagId[]: Iterable[int]
        childTags: bool  # noqa: N815
        # artistId[]: Iterable[int]
        artistParticipationStatus: ArtistParticipationStatus  # noqa: N815
        childVoicebanks: bool
        includeMembers: bool
