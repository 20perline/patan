"""Async HTTP client with built-in retry support."""

import json
import re
from collections.abc import Mapping
from typing import Any

import httpx

from patan.utils.exceptions import (
    APIConnectionError,
    APINotFoundError,
    APIRateLimitError,
    APIResponseError,
    APITimeoutError,
    APIUnauthorizedError,
    APIUnavailableError,
)


class AsyncHttpClient:
    """Reusable async HTTP client with automatic retries."""

    def __init__(
        self,
        *,
        proxies: Mapping[str, str | None] | None = None,
        max_retries: int = 3,
        max_connections: int = 50,
        timeout: float = 10,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        """Initialize HTTP client with retry support.

        Args:
            proxies: Proxy settings for HTTP/HTTPS.
            max_retries: Maximum number of retry attempts (default: 3).
            max_connections: Maximum concurrent connections (default: 50).
            timeout: Request timeout in seconds (default: 10).
            headers: Default headers to include in requests.
        """
        self.proxies = {key: value for key, value in (proxies or {}).items() if value} or None
        self.client = httpx.AsyncClient(
            headers=dict(headers or {}),
            proxy=self.proxies.get("https://") if self.proxies else None,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=max_connections),
            transport=httpx.AsyncHTTPTransport(retries=max_retries),
            follow_redirects=True,
        )

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Make HTTP request with automatic error mapping.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL.
            **kwargs: Additional arguments passed to httpx.

        Returns:
            HTTP response object.

        Raises:
            APINotFoundError: 404 status code.
            APIUnauthorizedError: 401 status code.
            APITimeoutError: Request timeout.
            APIRateLimitError: 429 status code.
            APIUnavailableError: 503 status code.
            APIConnectionError: Connection failure.
            APIResponseError: Other HTTP errors.
        """
        try:
            response = await self.client.request(method, url, **kwargs)
            if not response.content:
                raise APIResponseError(f"empty response from {response.url}")
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            raise APITimeoutError(f"timeout requesting {url}") from exc
        except httpx.ConnectError as exc:
            raise APIConnectionError(f"failed to connect to {url}") from exc
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.RequestError as exc:
            raise APIConnectionError(f"failed to request {url}") from exc

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        """Make POST request."""
        return await self.request("POST", url, **kwargs)

    @staticmethod
    def parse_json(response: httpx.Response) -> dict[str, Any]:
        """Parse JSON from response with fallback for malformed JSON.

        Args:
            response: HTTP response object.

        Returns:
            Parsed JSON dictionary.

        Raises:
            APIResponseError: If JSON parsing fails.
        """
        try:
            return response.json()
        except json.JSONDecodeError:
            # Try to extract JSON from text (some APIs return JSON in HTML)
            match = re.search(r"\{.*\}", response.text, re.DOTALL)
            if not match:
                raise APIResponseError(f"failed to parse json from {response.url}") from None
            try:
                return json.loads(match.group())
            except json.JSONDecodeError as exc:
                raise APIResponseError(f"failed to parse json from {response.url}") from exc

    @staticmethod
    def _map_http_error(exc: httpx.HTTPStatusError) -> Exception:
        """Map HTTP status codes to custom exceptions.

        Args:
            exc: HTTPStatusError from httpx.

        Returns:
            Mapped exception instance.
        """
        status_code = exc.response.status_code
        if status_code == httpx.codes.NOT_FOUND:
            return APINotFoundError(f"HTTP {status_code}")
        if status_code == httpx.codes.UNAUTHORIZED:
            return APIUnauthorizedError(f"HTTP {status_code}")
        if status_code == httpx.codes.REQUEST_TIMEOUT:
            return APITimeoutError(f"HTTP {status_code}")
        if status_code == httpx.codes.TOO_MANY_REQUESTS:
            return APIRateLimitError(f"HTTP {status_code}")
        if status_code == httpx.codes.SERVICE_UNAVAILABLE:
            return APIUnavailableError(f"HTTP {status_code}")
        return APIResponseError(f"HTTP {status_code}")

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self) -> "AsyncHttpClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
