from __future__ import annotations

from datetime import datetime

from .artist_contract import ArtistContract
from .artist_link_type import ArtistLinkType
from .artist_type import ArtistType
from .content_language_preference import ContentLanguagePreference
from .entry_thumb_for_api_contract import EntryThumbForApiContract
from .localized_string_with_id_contract import LocalizedStringWithIdContract
from .tag_usage_for_api_contract import TagUsageForApiContract
from .web_link_for_api_contract import WebLinkForApiContract


class ArtistForApiContract(ArtistContract, frozen=True, kw_only=True):
    create_date: datetime
    default_name_language: ContentLanguagePreference
    artist_links: tuple[ArtistLinkType, ...] | None = None
    artist_reverse_links: tuple[ArtistType, ...] | None = None
    base_voicebank: ArtistContract | None = None
    default_name: str | None = None
    description: str | None = None
    main_picture: EntryThumbForApiContract | None = None
    merged_to: int | None = None
    names: tuple[LocalizedStringWithIdContract, ...] | None = None
    # relations
    tags: tuple[TagUsageForApiContract, ...] | None = None
    web_links: tuple[WebLinkForApiContract, ...] | None = None
