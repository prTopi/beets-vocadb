from __future__ import annotations

import weakref
from functools import cache
from typing import TYPE_CHECKING, TypeVar

import httpx
import msgspec

if TYPE_CHECKING:
    from logging import Logger


T = TypeVar("T")


class ApiClient:
    """
    Generic API client using httpx and msgspec
    """

    def __init__(
        self,
        user_agent: str,
        base_url: httpx.URL | str,
        logger: Logger,
        timeout: float = 10,
    ) -> None:
        self._log: Logger = logger
        self.default_headers: httpx.Headers = httpx.Headers(
            headers={
                "accept": "application/json",
            }
        )
        self.user_agent = user_agent
        self.base_url: str | httpx.URL = base_url
        self.client: httpx.Client = httpx.Client(
            base_url=httpx.URL(url=self.base_url),
            http2=True,
            timeout=timeout,
        )
        _ = weakref.finalize(self, self.close)

    @property
    def user_agent(self) -> str:
        """User agent for this API client"""
        return self.default_headers["User-Agent"]

    @user_agent.setter
    def user_agent(self, value: str) -> None:
        self.default_headers["User-Agent"] = value

    @classmethod
    @cache
    def _get_decoder(cls, target_type: type[T]) -> msgspec.json.Decoder[T]:
        """Caches and returns a decoder for the specified type"""
        return msgspec.json.Decoder(type=target_type)

    def decode(self, content: str, target_type: type[T]) -> T:
        decoder: msgspec.json.Decoder[T] = self._get_decoder(
            target_type=target_type
        )
        return decoder.decode(content)

    def call_api(
        self,
        relative_path: str,
        params: httpx.QueryParams,
        return_type: type[T],
        headers: httpx.Headers | None = None,
    ) -> T | None:
        """Makes a GET request to the API and returns structured response data.

        Args:
            relative_path: API endpoint path to request
            params: instance of (a subclass of) ParamsBase

        Returns:
            Structured response data if successful, None if request fails
        """
        if not headers:
            headers = httpx.Headers()
        headers.update(headers=self.default_headers)

        try:
            request: httpx.Request = self.client.build_request(
                method="GET", url=relative_path, headers=headers, params=params
            )
            self._log.debug(f"url: {request.url}")
            response: httpx.Response = self.client.send(request=request)
            _ = response.raise_for_status()
        except httpx.HTTPError as e:
            self._log.error("Error fetching data - {}", e)
            return
        try:
            return self.decode(content=response.text, target_type=return_type)
        except msgspec.DecodeError:
            import json

            self._log.debug(json.dumps(response.json(), indent=2))

    # TODO: better error handling

    def close(self) -> None:
        self._log.debug("Closing {}", self.client)
        self.client.close()
