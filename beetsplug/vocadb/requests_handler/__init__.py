from __future__ import annotations

import weakref
from cattrs import structure
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from logging import Logger
    from typing_extensions import TypeAlias
    from .models import APIObjectT

ParamsT: TypeAlias = dict[str, str]


class RequestsHandler:
    """
    An interface to the VocaDB API.
    Can be subclassed to use a different instance.
    """

    base_url: str = "https://vocadb.net/"
    api_base_url: str = "https://vocadb.net/api/"

    user_agent: str

    def __init__(self, user_agent: str, logger: Logger) -> None:
        self.user_agent = user_agent
        self._log: Logger = logger
        self.client: httpx.Client = httpx.Client(
            base_url=self.api_base_url,
            headers={"accept": "application/json", "User-Agent": self.user_agent},
            http2=True,
            timeout=10,
        )
        _ = weakref.finalize(self, self.client.close)

    def __init_subclass__(
        cls, base_url: str, api_url: str
    ) -> None:
        cls.base_url = base_url
        cls.api_base_url = api_url

    def _get(
        self, relative_path: str, params: ParamsT, cl: type[APIObjectT]
    ) -> APIObjectT | None:
        """Makes a GET request to the API and returns structured response data.

        Args:
            path: API endpoint path to request
            params: Dictionary of URL parameters

        Returns:
            Structured response data if successful, None if request fails
        """
        try:
            response: httpx.Response = self.client.get(
                relative_path, params=params
            ).raise_for_status()

            return structure(response.json(), cl=cl)

        except httpx.HTTPError as e:
            self._log.error("Error fetching data - {}", e)

        return None

    # TODO: more specific methods with better error handling
