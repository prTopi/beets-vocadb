from __future__ import annotations

from collections.abc import Hashable
from functools import cache, cached_property
from typing import TYPE_CHECKING, TypeVar

import msgspec
import niquests
from urllib3 import Retry

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping
    from logging import Logger


H = TypeVar(name="H", bound=Hashable)


class ApiClient:
    """
    Generic API client using niquests and msgspec
    """

    def __init__(
        self,
        user_agent: str,
        base_url: str,
        logger: Logger,
    ) -> None:
        self._log: Logger = logger
        self.default_headers: MutableMapping[str, str] = {
            "accept": "application/json",
        }
        self.user_agent = user_agent
        self.base_url: str = base_url
        self.closed: bool = True

    @cached_property
    def session(self) -> niquests.Session:
        self.closed = False
        return niquests.Session(
            base_url=self.base_url,
            retries=Retry(total=6, backoff_factor=0.5),
        )

    @property
    def user_agent(self) -> str:
        """User agent for this API client"""
        return self.default_headers["User-Agent"]

    @user_agent.setter
    def user_agent(self, value: str) -> None:
        self.default_headers["User-Agent"] = value

    @classmethod
    @cache
    def _get_decoder(cls, target_type: type[H]) -> msgspec.json.Decoder[H]:
        """Caches and returns a decoder for the specified type"""
        return msgspec.json.Decoder(type=target_type)

    def decode(self, content: str, target_type: type[H]) -> H:
        decoder: msgspec.json.Decoder[H] = self._get_decoder(
            target_type=target_type
        )
        return decoder.decode(content)

    def call_api(
        self,
        relative_path: str,
        params: Mapping[str, object],
        return_type: type[H],
        headers: MutableMapping[str, str] | None = None,
    ) -> H | None:
        """Makes a GET request to the API and returns structured response data.

        Args:
            relative_path: API endpoint path to request
            params: instance of (a subclass of) ParamsBase

        Returns:
            Structured response data if successful, None if request fails
        """
        if not headers:
            headers = {}
        headers.update(self.default_headers)

        try:
            request: niquests.PreparedRequest = self.session.prepare_request(
                request=niquests.Request(
                    method="GET",
                    url=relative_path,
                    headers=headers,
                    params={
                        key: (
                            [str(item) for item in value]  # pyright: ignore[reportUnknownArgumentType,reportUnknownVariableType]
                            if isinstance(value, list | set)
                            else str(value)
                        )
                        for key, value in params.items()
                    },
                )
            )
            self._log.debug(msg=f"url: {request.url}")
            response: niquests.Response = self.session.send(request=request)
            _ = response.raise_for_status()
        except niquests.HTTPError as e:
            self._log.error("Error fetching {} - {}", return_type.__name__, e)
            return None
        try:
            return self.decode(
                content=response.text or "", target_type=return_type
            )
        except msgspec.DecodeError as e:
            self._log.info("Error decoding {}: {}", return_type.__name__, e)
            self._log.debug("{}", msgspec.json.format(response.text or ""))
            return None

    # TODO: better error handling

    def close(self) -> None:
        if not self.closed:
            self.session.close()
            self.closed = True
