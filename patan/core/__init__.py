from patan.core.config import find_project_root, load_env_config
from patan.core.dedup import ContentDeduplicator, MetadataDeduplicator, URLDeduplicator
from patan.core.downloader import DownloadProgressDisplay, DownloadProgressLogger, VideoDownloader
from patan.core.http import AsyncHttpClient
from patan.core.logging import configure_logging, get_logger, logger
from patan.core.models import ChannelConfig, CommentInfo, UserInfo, VideoMetadata
from patan.core.scheduler import AsyncTaskQueue, TaskScheduler

__all__ = [
    # HTTP & Config
    "AsyncHttpClient",
    "find_project_root",
    "load_env_config",
    "logger",
    "get_logger",
    "configure_logging",
    # Models
    "VideoMetadata",
    "UserInfo",
    "CommentInfo",
    "ChannelConfig",
    # Downloader
    "VideoDownloader",
    "DownloadProgressDisplay",
    "DownloadProgressLogger",
    # Scheduler
    "TaskScheduler",
    "AsyncTaskQueue",
    # Deduplication
    "ContentDeduplicator",
    "URLDeduplicator",
    "MetadataDeduplicator",
]
