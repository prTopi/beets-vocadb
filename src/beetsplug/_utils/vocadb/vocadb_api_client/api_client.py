from __future__ import annotations

import posixpath
import time
from collections.abc import Iterable, Sequence
from functools import cache, cached_property
from typing import TYPE_CHECKING

import msgspec
import niquests
from urllib3 import Retry

if TYPE_CHECKING:
    from collections.abc import Hashable, Mapping, MutableMapping
    from logging import Logger
    from typing import TypeVar

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

    def _normalize_params(
        self, params: Mapping[str, object]
    ) -> dict[str, str | list[str]]:
        """Turn params values into str or list[str]."""
        return {
            key: (
                [str(item) for item in value]
                if not isinstance(value, str) and isinstance(value, Iterable)
                else str(value)
            )
            for key, value in params.items()
        }

    def prepare_request(
        self,
        *paths: str,
        params: Mapping[str, object | tuple[object]],
        headers: MutableMapping[str, str] | None = None,
    ) -> niquests.PreparedRequest:
        """Prepare a niquests PreparedRequest using the normalized params."""
        if not headers:
            headers = {}
        # preserve previous behavior: default_headers are applied into headers
        headers.update(self.default_headers)
        relative_path = posixpath.join(*paths)

        request: niquests.PreparedRequest = self.session.prepare_request(
            request=niquests.Request(
                method="GET",
                url=relative_path,
                headers=headers,
                params=self._normalize_params(params),
            )
        )
        return request

    def send_requests(
        self,
        prepared_requests: Sequence[niquests.PreparedRequest | None],
    ) -> list[niquests.Response | None]:
        t0: float = time.monotonic()
        if len(prepared_requests) == 1 and (
            prepared_request := prepared_requests[0]
        ):
            responses: list[niquests.Response | None] = [
                self.session.send(request=prepared_request)
            ]
        else:
            responses = [
                (
                    self.session.send(
                        request=prepared_request, multiplexed=True
                    )
                    if prepared_request
                    else None
                )
                for prepared_request in prepared_requests
            ]
        self._log.debug(
            f"sending {len(responses)} requests took {time.monotonic() - t0:.2f}s"
        )
        return responses

    def decode(self, content: str | None, target_type: type[H]) -> H | None:
        if not content:
            return None
        decoder: msgspec.json.Decoder[H] = self._get_decoder(
            target_type=target_type
        )
        return decoder.decode(content)

    def decode_response(
        self, response: niquests.Response | None, target_type: type[H]
    ) -> H | None:
        """Handle HTTP errors and decode the response body (returns None on failure)."""
        if not response:
            return None
        try:
            response = response.raise_for_status()
            try:
                self._log.debug(msg=f"url: {response.history[0].url}")
            except IndexError:
                self._log.debug(msg=f"url: {response.url}")
        except niquests.HTTPError as e:
            if response.status_code == 404:
                if (original_url := response.history[0].url) and (
                    redirect_url := response.url
                ):
                    e = str(e).replace(redirect_url, original_url)
            self._log.error("Error fetching {} - {}", target_type.__name__, e)
            return None
        try:
            return self.decode(
                content=response.text or "", target_type=target_type
            )
        except msgspec.DecodeError as e:
            self._log.info("Error decoding {}: {}", target_type.__name__, e)
            self._log.debug("{}", msgspec.json.format(response.text or ""))
            return None

    def call_api(
        self,
        *paths: str,
        params: Mapping[str, object],
        return_type: type[H],
        headers: MutableMapping[str, str] | None = None,
    ) -> H | None:
        """Makes a GET request to the API and returns structured response data.

        Args:
            paths: components of API endpoint path to request
            params: instance of (a subclass of) ParamsBase

        Returns:
            Structured response data if successful, None if request fails
        """
        return self.decode_response(
            response=self.session.send(
                request=self.prepare_request(
                    *paths, params=params, headers=headers
                )
            ),
            target_type=return_type,
        )

    # TODO: better error handling

    def close(self) -> None:
        if not self.closed:
            self.session.close()
            self.closed = True
