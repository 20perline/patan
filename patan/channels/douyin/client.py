"""Douyin API client with URL extraction and HTTP request handling."""

import asyncio
import re
from collections.abc import Mapping
from typing import TypeAlias
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel

from patan.core.http import AsyncHttpClient
from patan.channels.douyin.config import DouyinConfig, DouyinAPIEndpoints
from patan.channels.douyin.crypto import (
    build_abogus_value,
    build_xbogus_signed_url,
    generate_ms_token,
    generate_ttwid,
    generate_verify_fp,
    generate_web_id,
    sign_url_with_xbogus,
)
from patan.channels.douyin.models import (
    BaseRequestModel,
    LiveRoomRanking,
    PostComments,
    PostCommentsReply,
    PostDetail,
    UserCollection,
    UserLike,
    UserLive,
    UserLive2,
    UserMix,
    UserPost,
    UserProfile,
)
from patan.utils import extract_valid_urls
from patan.utils.exceptions import (
    APIConnectionError,
    APINotFoundError,
    APIResponseError,
    APIUnauthorizedError,
    APIUnavailableError,
)

JsonObject: TypeAlias = dict[str, object]

# URL patterns for extraction
_USER_URL_PATTERN = re.compile(r"user/([^/?]*)")
_REDIRECT_SEC_UID_PATTERN = re.compile(r"sec_uid=([^&]*)")
_VIDEO_URL_PATTERNS = (
    re.compile(r"video/([^/?]*)"),
    re.compile(r"[?&]vid=(\d+)"),
    re.compile(r"note/([^/?]*)"),
    re.compile(r"modal_id=([0-9]+)"),
)
_LIVE_URL_PATTERNS = (
    re.compile(r"live/([^/?]*)"),
    re.compile(r"http[s]?://live.douyin.com/(\d+)"),
    re.compile(r"reflow/([^/?]*)"),
)


class DouyinClient:
    """Client for interacting with Douyin API."""

    def __init__(self, config: DouyinConfig | None = None) -> None:
        """Initialize client with optional configuration."""
        self.config = config or DouyinConfig.load()

    # ========== Video & User Data ==========

    async def fetch_video_detail(self, aweme_id: str) -> JsonObject:
        """Fetch detailed information about a specific video."""
        return await self._signed_get(DouyinAPIEndpoints.POST_DETAIL, PostDetail(aweme_id=aweme_id), signer="a_bogus")

    async def fetch_user_post_videos(self, sec_user_id: str, max_cursor: int, count: int) -> JsonObject:
        """Fetch videos posted by a user."""
        model = UserPost(sec_user_id=sec_user_id, max_cursor=max_cursor, count=count)
        return await self._signed_get(DouyinAPIEndpoints.USER_POST, model, signer="a_bogus")

    async def fetch_user_like_videos(self, sec_user_id: str, max_cursor: int, count: int) -> JsonObject:
        """Fetch videos liked by a user."""
        model = UserLike(sec_user_id=sec_user_id, max_cursor=max_cursor, count=count)
        return await self._signed_get(DouyinAPIEndpoints.USER_FAVORITE_A, model, signer="a_bogus")

    async def fetch_user_collection_videos(self, cookie: str, cursor: int = 0, count: int = 20) -> JsonObject:
        """Fetch videos collected by a user."""
        return await self._signed_post(
            DouyinAPIEndpoints.USER_COLLECTION,
            UserCollection(cursor=cursor, count=count),
            config=self.config.with_cookie(cookie),
        )

    async def fetch_user_mix_videos(self, mix_id: str, cursor: int = 0, count: int = 20) -> JsonObject:
        """Fetch videos from a mix/collection."""
        return await self._signed_get(DouyinAPIEndpoints.MIX_AWEME, UserMix(mix_id=mix_id, cursor=cursor, count=count))

    # ========== Live Stream ==========

    async def fetch_user_live_videos(self, webcast_id: str, room_id_str: str = "") -> JsonObject:
        """Fetch live stream information."""
        return await self._signed_get(DouyinAPIEndpoints.LIVE_INFO, UserLive(web_rid=webcast_id, room_id_str=room_id_str))

    async def fetch_user_live_videos_by_room_id(self, room_id: str) -> JsonObject:
        """Fetch live stream by room ID."""
        return await self._signed_get(DouyinAPIEndpoints.LIVE_INFO_ROOM_ID, UserLive2(room_id=room_id))

    async def fetch_live_gift_ranking(self, room_id: str, rank_type: int = 30) -> JsonObject:
        """Fetch gift ranking for a live room."""
        model = LiveRoomRanking(room_id=int(room_id), rank_type=rank_type)
        return await self._signed_get(DouyinAPIEndpoints.LIVE_GIFT_RANK, model)

    # ========== User Profile ==========

    async def fetch_user_profile(self, sec_user_id: str) -> JsonObject:
        """Fetch user profile information."""
        return await self._signed_get(DouyinAPIEndpoints.USER_DETAIL, UserProfile(sec_user_id=sec_user_id))

    # ========== Comments ==========

    async def fetch_video_comments(self, aweme_id: str, cursor: int = 0, count: int = 20) -> JsonObject:
        """Fetch comments for a video."""
        return await self._signed_get(
            DouyinAPIEndpoints.POST_COMMENT, PostComments(aweme_id=aweme_id, cursor=cursor, count=count)
        )

    async def fetch_video_comments_reply(self, item_id: str, comment_id: str, cursor: int = 0,
                                         count: int = 20) -> JsonObject:
        """Fetch replies to a comment."""
        model = PostCommentsReply(item_id=item_id, comment_id=comment_id, cursor=cursor, count=count)
        return await self._signed_get(DouyinAPIEndpoints.POST_COMMENT_REPLY, model)

    # ========== Search & Discovery ==========

    async def fetch_hot_search_result(self) -> JsonObject:
        """Fetch hot search trending topics."""
        return await self._signed_get(DouyinAPIEndpoints.DOUYIN_HOT_SEARCH, BaseRequestModel())

    # ========== Token & ID Generation ==========

    async def generate_ms_token(self) -> dict[str, str]:
        """Generate msToken."""
        return {"ms_token": generate_ms_token(self.config)}

    async def generate_ttwid(self) -> dict[str, str]:
        """Generate ttwid."""
        return {"ttwid": generate_ttwid(self.config)}

    async def generate_verify_fp(self) -> dict[str, str]:
        """Generate verify_fp fingerprint."""
        return {"verify_fp": generate_verify_fp()}

    async def generate_web_id(self) -> dict[str, str]:
        """Generate web_id."""
        return {"web_id": generate_web_id()}

    async def build_xbogus_url(self, url: str, user_agent: str) -> dict[str, str]:
        """Build URL with X-Bogus signature."""
        signed_url = sign_url_with_xbogus(url, user_agent)
        return {"url": signed_url, "x_bogus": signed_url.split("&X-Bogus=")[1], "user_agent": user_agent}

    async def build_abogus_url(self, url: str, user_agent: str) -> dict[str, str]:
        """Build URL with A-Bogus signature."""
        endpoint, query = url.split("?", maxsplit=1)
        params = dict(item.split("=") for item in query.split("&"))
        params["msToken"] = ""
        a_bogus = build_abogus_value(params, user_agent)
        return {"url": f"{endpoint}?{urlencode(params)}&a_bogus={a_bogus}", "a_bogus": a_bogus, "user_agent": user_agent}

    # ========== URL ID Extraction ==========

    async def get_sec_user_id(self, url: str) -> str:
        """Extract sec_user_id from Douyin user URL."""
        parsed_url = _validate_url(url)
        redirected_url, status_code = await _request_redirected_url(parsed_url, self.config)
        pattern = _REDIRECT_SEC_UID_PATTERN if "v.douyin.com" in parsed_url else _USER_URL_PATTERN
        if status_code in {200, 444}:
            match = pattern.search(redirected_url)
            if match:
                return match.group(1)
            raise APIResponseError("sec_user_id not found in redirected url")
        if status_code == 401:
            raise APIUnauthorizedError("unauthorized request")
        if status_code == 404:
            raise APINotFoundError("endpoint not found")
        if status_code == 503:
            raise APIUnavailableError("service unavailable")
        raise APIResponseError(f"unexpected status code: {status_code}")

    async def get_sec_user_ids(self, urls: list[str]) -> list[str]:
        """Extract sec_user_id from multiple Douyin user URLs."""
        if not isinstance(urls, list):
            raise TypeError("urls must be a list")
        if not urls:
            raise APINotFoundError("invalid url list")
        return await asyncio.gather(*(self.get_sec_user_id(url) for url in urls))

    async def get_aweme_id(self, url: str) -> str:
        """Extract aweme_id from Douyin video URL."""
        if not isinstance(url, str):
            raise TypeError("url must be a string")
        try:
            async with httpx.AsyncClient(transport=httpx.AsyncHTTPTransport(retries=5), timeout=10,
                                         follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.RequestError as exc:
            raise APIConnectionError(f"failed to request {url}") from exc
        return _extract_first_match(str(response.url), _VIDEO_URL_PATTERNS, "aweme_id not found in redirected url")

    async def get_aweme_ids(self, urls: list[str]) -> list[str]:
        """Extract aweme_id from multiple Douyin video URLs."""
        if not isinstance(urls, list):
            raise TypeError("urls must be a list")
        if not urls:
            raise APINotFoundError("invalid url list")
        return await asyncio.gather(*(self.get_aweme_id(url) for url in urls))

    async def get_webcast_id(self, url: str) -> str:
        """Extract webcast_id from Douyin live URL."""
        parsed_url = _validate_url(url)
        redirected_url, _ = await _request_redirected_url(parsed_url, self.config)
        return _extract_first_match(redirected_url, _LIVE_URL_PATTERNS, "webcast_id not found in redirected url")

    async def get_webcast_ids(self, urls: list[str]) -> list[str]:
        """Extract webcast_id from multiple Douyin live URLs."""
        if not isinstance(urls, list):
            raise TypeError("urls must be a list")
        if not urls:
            raise APINotFoundError("invalid url list")
        return await asyncio.gather(*(self.get_webcast_id(url) for url in urls))

    # ========== Configuration ==========

    async def update_cookie(self, cookie: str) -> None:
        """Update the cookie in current configuration."""
        self.config = self.config.with_cookie(cookie)

    # ========== Internal Methods ==========

    async def _signed_get(
        self,
        endpoint: str,
        model: BaseModel,
        *,
        signer: str = "x_bogus",
        config: DouyinConfig | None = None,
    ) -> JsonObject:
        """Internal method for signed GET requests."""
        active_config = config or self.config
        request_url = self._build_signed_url(endpoint, model, active_config, signer=signer)
        crawler: _CrawlerWrapper = _CrawlerWrapper(proxies=active_config.proxies, headers=active_config.headers)
        async with crawler:
            return await crawler.fetch_get_json(request_url)

    async def _signed_post(
        self,
        endpoint: str,
        model: BaseModel,
        *,
        signer: str = "x_bogus",
        config: DouyinConfig | None = None,
    ) -> JsonObject:
        """Internal method for signed POST requests."""
        active_config = config or self.config
        request_url = self._build_signed_url(endpoint, model, active_config, signer=signer)
        crawler: _CrawlerWrapper = _CrawlerWrapper(proxies=active_config.proxies, headers=active_config.headers)
        async with crawler:
            return await crawler.fetch_post_json(request_url)

    def _build_signed_url(self, endpoint: str, model: BaseModel, config: DouyinConfig, *,
                          signer: str) -> str:
        """Build signed URL with appropriate signature method."""
        params = model.model_dump(by_alias=True)
        params.setdefault("msToken", "")
        user_agent = config.headers["User-Agent"]
        if signer == "a_bogus":
            a_bogus = build_abogus_value(params, user_agent)
            return f"{endpoint}?{urlencode(params)}&a_bogus={a_bogus}"
        return build_xbogus_signed_url(endpoint, params, user_agent)


# ========== Internal Helper Classes ==========

class _CrawlerWrapper(AsyncHttpClient):
    """Internal wrapper for HTTP requests (formerly BaseCrawler)."""

    def __init__(
        self,
        *,
        proxies: Mapping[str, str | None] | None = None,
        max_retries: int = 3,
        max_connections: int = 50,
        timeout: float = 10,
        headers: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(
            proxies=proxies,
            max_retries=max_retries,
            max_connections=max_connections,
            timeout=timeout,
            headers=headers,
        )

    async def fetch_get_json(self, endpoint: str) -> JsonObject:
        """Fetch and parse JSON from GET request."""
        return self.parse_json(await self.get(endpoint))

    async def fetch_post_json(
        self,
        endpoint: str,
        params: Mapping[str, object] | None = None,
        data: object | None = None,
    ) -> JsonObject:
        """Fetch and parse JSON from POST request."""
        return self.parse_json(await self.post(endpoint, json=dict(params or {}), data=data))


# ========== URL Extraction Helpers ==========

def _validate_url(url: str) -> str:
    """Validate and normalize URL."""
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    parsed_url = extract_valid_urls(url)
    if parsed_url is None:
        raise APINotFoundError("invalid url")
    if isinstance(parsed_url, list):
        raise APINotFoundError("invalid url")
    return parsed_url


def _extract_first_match(url: str, patterns: tuple[re.Pattern[str], ...], error_message: str) -> str:
    """Extract first matching pattern from URL."""
    for pattern in patterns:
        match = pattern.search(url)
        if match:
            return match.group(1)
    raise APIResponseError(error_message)


async def _request_redirected_url(url: str, config: DouyinConfig) -> tuple[str, int]:
    """Request URL and return final redirected URL with status code."""
    try:
        async with httpx.AsyncClient(
            proxy=config.proxies.get("https://"),
            transport=httpx.AsyncHTTPTransport(retries=5),
            timeout=10,
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
    except httpx.RequestError as exc:
        raise APIConnectionError(f"failed to request {url}") from exc
    return str(response.url), response.status_code
