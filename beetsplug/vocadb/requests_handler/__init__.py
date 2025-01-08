from __future__ import annotations

import weakref

import sys
from typing import TYPE_CHECKING, TypeVar, cast

import httpx
import msgspec

if not sys.version_info < (3, 11):
    from enum import StrEnum
else:
    from enum import Enum
    class StrEnum(str, Enum):
        pass


if TYPE_CHECKING:
    from logging import Logger
    from typing import ClassVar
    from typing_extensions import TypeAlias

APIObjectT = TypeVar("APIObjectT", bound=msgspec.Struct)
ParamsT: TypeAlias = dict[str, str]


def dec_hook(type: type, obj: object) -> object:
    if type is StrEnum and isinstance(obj, str):
        if not obj:
            return []
        return [StrEnum(val.strip()) for val in obj.split(",") if val.strip()]
    else:
        # Raise a NotImplementedError for other types
        raise NotImplementedError(f"Objects of type {type} are not supported")


class RequestsHandler:
    """
    An interface to the VocaDB API.
    Can be subclassed to use a different instance.
    """

    base_url: str = "https://vocadb.net/"
    api_base_url: str = "https://vocadb.net/api/"

    _decoders: ClassVar[
        dict[type[msgspec.Struct], msgspec.json.Decoder[msgspec.Struct]]
    ] = {}

    def __init__(self, user_agent: str, logger: Logger) -> None:
        self._log: Logger = logger
        self._client: httpx.Client = httpx.Client(
            base_url=self.api_base_url,
            headers={"accept": "application/json", "User-Agent": user_agent},
            http2=True,
            timeout=10,
        )
        self._client.base_url = self.api_base_url
        _ = weakref.finalize(self, self.close)

    def __init_subclass__(cls, base_url: str, api_url: str) -> None:
        cls.base_url = base_url
        cls.api_base_url = api_url

    @classmethod
    def get_decoder(cls, type: type[APIObjectT]) -> msgspec.json.Decoder[APIObjectT]:
        """Caches and returns a decoder for the specified type"""
        decoder = msgspec.json.Decoder[APIObjectT](type=type, dec_hook=dec_hook)
        cls._decoders[type] = cast(msgspec.json.Decoder[msgspec.Struct], decoder)
        return decoder

    def _get(
        self, relative_path: str, params: ParamsT, type: type[APIObjectT]
    ) -> APIObjectT | None:
        """Makes a GET request to the API and returns structured response data.

        Args:
            path: API endpoint path to request
            params: Dictionary of URL parameters

        Returns:
            Structured response data if successful, None if request fails
        """

        try:
            response: httpx.Response = self._client.get(relative_path, params=params)
            _ = response.raise_for_status()
        except httpx.HTTPError as e:
            self._log.error("Error fetching data - {}", e)
            return None

        decoder: msgspec.json.Decoder[APIObjectT]
        try:
            decoder = cast(msgspec.json.Decoder[APIObjectT], self._decoders[type])
        except KeyError:
            self._log.debug("Getting decoder for {}", type)
            decoder = self.get_decoder(type)
        return decoder.decode(response.content)

    # TODO: more specific methods with better error handling

    def close(self):
        self._log.debug("Closing {}", self._client)
        self._client.close()
