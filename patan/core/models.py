"""统一的数据模型定义.

所有 channel 都应该适配成这些统一的数据格式，方便上层应用处理。
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    """视频元数据的统一格式."""

    title: str
    description: str
    author: str
    author_id: str
    video_url: str
    cover_url: str | None = None
    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    play_count: int = 0
    created_at: datetime | None = None
    duration: int | None = None  # 秒

    # 平台特定字段（可选）
    extra: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class UserInfo(BaseModel):
    """用户信息的统一格式."""

    nickname: str
    user_id: str
    signature: str | None = None
    avatar_url: str | None = None
    follower_count: int = 0
    following_count: int = 0
    like_count: int = 0  # 获赞总数
    video_count: int = 0
    is_verified: bool = False
    location: str | None = None

    # 平台特定字段
    extra: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class CommentInfo(BaseModel):
    """评论信息的统一格式."""

    comment_id: str
    content: str
    author_nickname: str
    author_id: str
    like_count: int = 0
    reply_count: int = 0
    created_at: datetime | None = None
    parent_comment_id: str | None = None

    # 平台特定字段
    extra: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True


class ChannelConfig(BaseModel):
    """Channel 配置的统一格式."""

    platform_name: str  # 如 "douyin", "bilibili"
    enabled: bool = True
    max_concurrent_requests: int = 5
    request_timeout: float = 10.0
    retry_attempts: int = 3
    proxy_enabled: bool = False

    # 平台特定配置
    extra: dict[str, Any] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
