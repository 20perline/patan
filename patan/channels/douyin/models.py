"""Pydantic models for Douyin API requests and responses."""

from typing import TypeAlias

from pydantic import BaseModel, ConfigDict, Field

from patan.channels.douyin.crypto import generate_fake_ms_token, generate_verify_fp

JsonObject: TypeAlias = dict[str, object]


class PatanModel(BaseModel):
    """Base model with common configuration."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class BaseRequestModel(PatanModel):
    """Base model for standard API requests."""

    device_platform: str = "webapp"
    aid: str = "6383"
    channel: str = "channel_pc_web"
    pc_client_type: int = 1
    version_code: str = "290100"
    version_name: str = "29.1.0"
    cookie_enabled: str = "true"
    screen_width: int = 1920
    screen_height: int = 1080
    browser_language: str = "zh-CN"
    browser_platform: str = "Win32"
    browser_name: str = "Chrome"
    browser_version: str = "130.0.0.0"
    browser_online: str = "true"
    engine_name: str = "Blink"
    engine_version: str = "130.0.0.0"
    os_name: str = "Windows"
    os_version: str = "10"
    cpu_core_num: int = 12
    device_memory: int = 8
    platform: str = "PC"
    downlink: str = "10"
    effective_type: str = "4g"
    from_user_page: str = "1"
    locate_query: str = "false"
    need_time_list: str = "1"
    pc_libra_divert: str = "Windows"
    publish_video_strategy_type: str = "2"
    round_trip_time: str = "0"
    show_live_replay_strategy: str = "1"
    time_list_query: str = "0"
    whale_cut_token: str = ""
    update_version_code: str = "170400"
    ms_token: str = Field(default="", serialization_alias="msToken")


class BaseLiveModel(PatanModel):
    """Base model for live stream requests."""

    aid: str = "6383"
    app_name: str = "douyin_web"
    live_id: int = 1
    device_platform: str = "web"
    language: str = "zh-CN"
    cookie_enabled: str = "true"
    screen_width: int = 1920
    screen_height: int = 1080
    browser_language: str = "zh-CN"
    browser_platform: str = "Win32"
    browser_name: str = "Edge"
    browser_version: str = "119.0.0.0"
    enter_source: str = ""
    is_need_double_stream: str = "false"


class BaseLiveModel2(PatanModel):
    """Alternative base model for live stream requests."""

    verify_fp: str = Field(default_factory=generate_verify_fp, serialization_alias="verifyFp")
    type_id: str = "0"
    live_id: str = "1"
    sec_user_id: str = ""
    version_code: str = "99.99.99"
    app_id: str = "1128"
    ms_token: str = Field(default_factory=generate_fake_ms_token, serialization_alias="msToken")


# ========== User Models ==========

class UserProfile(BaseRequestModel):
    """User profile request."""

    sec_user_id: str


class UserPost(BaseRequestModel):
    """User posts request."""

    sec_user_id: str
    max_cursor: int
    count: int


class UserLike(BaseRequestModel):
    """User liked videos request."""

    sec_user_id: str
    max_cursor: int
    count: int


class UserCollection(BaseRequestModel):
    """User collection request."""

    cursor: int
    count: int


class UserMix(BaseRequestModel):
    """Mix/collection videos request."""

    mix_id: str
    cursor: int
    count: int


# ========== Post Models ==========

class PostDetail(BaseRequestModel):
    """Post detail request."""

    aweme_id: str


class PostComments(BaseRequestModel):
    """Post comments request."""

    aweme_id: str
    cursor: int = 0
    count: int = 20
    item_type: int = 0
    insert_ids: str = ""
    whale_cut_token: str = ""
    cut_version: int = 1
    rcFT: str = ""


class PostCommentsReply(BaseRequestModel):
    """Post comment replies request."""

    item_id: str
    comment_id: str
    cursor: int = 0
    count: int = 20
    item_type: int = 0


# ========== Live Models ==========

class UserLive(BaseLiveModel):
    """Live stream request by web_rid."""

    web_rid: str
    room_id_str: str


class UserLive2(BaseLiveModel2):
    """Live stream request by room_id."""

    room_id: str


class LiveRoomRanking(BaseRequestModel):
    """Live room gift ranking request."""

    room_id: int
    rank_type: int = 30
    webcast_sdk_version: int = 2450
