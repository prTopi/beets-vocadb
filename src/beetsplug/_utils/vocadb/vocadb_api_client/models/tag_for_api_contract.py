from __future__ import annotations

from datetime import datetime

from .content_language_selection import ContentLanguageSelection
from .english_translated_string_contract import EnglishTranslatedStringContract
from .entry_status import EntryStatus
from .entry_thumb_for_api_contract import EntryThumbForApiContract
from .localized_string_with_id_contract import LocalizedStringWithIdContract
from .tag_base_contract import TagBaseContract
from .web_link_for_api_contract import WebLinkForApiContract


class TagForApiContract(TagBaseContract, frozen=True, kw_only=True):
    create_date: datetime
    default_name_language: ContentLanguageSelection
    status: EntryStatus
    targets: int
    usage_count: int
    version: int
    aliased_to: TagBaseContract | None = None
    description: str | None = None
    main_picture: EntryThumbForApiContract | None = None
    names: tuple[LocalizedStringWithIdContract, ...] | None = None
    new_targets: tuple[str, ...] | None = None
    parent: TagBaseContract | None = None
    related_tags: tuple[TagBaseContract, ...] | None = None
    translated_description: EnglishTranslatedStringContract | None = None
    web_links: tuple[WebLinkForApiContract, ...] | None = None
