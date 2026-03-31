from patan.core.config import find_project_root, load_env_config
from patan.core.dedup import ContentDeduplicator, MetadataDeduplicator, URLDeduplicator
from patan.core.downloader import DownloadProgress, VideoDownloader
from patan.core.http import AsyncHttpClient
from patan.core.logging import get_logger, logger
from patan.core.models import ChannelConfig, CommentInfo, UserInfo, VideoMetadata
from patan.core.scheduler import AsyncTaskQueue, TaskScheduler

__all__ = [
    # HTTP & Config
    "AsyncHttpClient",
    "find_project_root",
    "load_env_config",
    "logger",
    "get_logger",
    # Models
    "VideoMetadata",
    "UserInfo",
    "CommentInfo",
    "ChannelConfig",
    # Downloader
    "VideoDownloader",
    "DownloadProgress",
    # Scheduler
    "TaskScheduler",
    "AsyncTaskQueue",
    # Deduplication
    "ContentDeduplicator",
    "URLDeduplicator",
    "MetadataDeduplicator",
]
