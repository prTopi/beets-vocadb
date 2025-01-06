from logging import Logger
import weakref
from cattrs import structure
from typing import Optional
from typing_extensions import LiteralString, TypeAlias

import httpx

from beets import __version__ as beets_version

from .models import APIObjectT

ParamsT: TypeAlias = dict[str, str]

USER_AGENT: str = f"beets/{beets_version} +https://beets.io/"
HEADERS: dict[str, str] = {"accept": "application/json", "User-Agent": USER_AGENT}
SONG_FIELDS: LiteralString = "Artists,CultureCodes,Tags,Bpm,Lyrics"


class RequestsHandler:
    """
    An interface to the VocaDB API.
    Can be subclassed to use a different instance.
    """

    base_url: str = "https://vocadb.net/"
    api_base_url: str = "https://vocadb.net/api/"
    user_agent: str = USER_AGENT

    def __init__(self, logger: Logger) -> None:
        self._log: Logger = logger
        self.client: httpx.Client = httpx.Client(
            base_url=self.api_base_url,
            headers={"accept": "application/json", "User-Agent": self.user_agent},
            http2=True,
            timeout=10,
        )
        _ = weakref.finalize(self, self.client.close)

    def __init_subclass__(
        cls, base_url: str, api_url: str, user_agent: Optional[str] = None
    ) -> None:
        cls.base_url = base_url
        cls.api_base_url = api_url
        if user_agent:
            cls.user_agent = user_agent

    def _get(
        self, relative_path: str, params: ParamsT, cl: type[APIObjectT]
    ) -> Optional[APIObjectT]:
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
            self._log.error("Error fetching data from {}\n - {}", e.request.url, e)

        return None
