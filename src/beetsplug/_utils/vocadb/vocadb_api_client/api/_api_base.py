from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import ClassVar

    from ..api_client import ApiClient


class ApiBase:
    path: ClassVar[str]

    def __init__(self, api_client: ApiClient) -> None:
        self.api_client: ApiClient = api_client

    def __init_subclass__(cls, path: str) -> None:
        cls.path = path
