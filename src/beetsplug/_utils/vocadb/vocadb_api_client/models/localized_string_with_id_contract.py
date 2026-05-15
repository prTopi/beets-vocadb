from __future__ import annotations

from .localized_string_contract import LocalizedStringContract


class LocalizedStringWithIdContract(
    LocalizedStringContract, frozen=True, kw_only=True
):
    id: int
