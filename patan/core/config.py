"""Configuration management using environment variables and .env files."""

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def find_project_root(start: str | Path) -> Path:
    """Find the project root directory by looking for pyproject.toml or .git."""
    current = Path(start).resolve()
    for path in (current, *current.parents):
        if (path / "pyproject.toml").exists() or (path / ".git").exists():
            return path
    return current.parent if current.is_file() else current


def load_env_config(start: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from .env file with environment variable fallback.

    Priority: environment variables > .env file > default values

    Supported environment variables:
    - COOKIE: Your authentication cookie
    - USER_AGENT: Custom User-Agent string
    - HTTP_PROXY: HTTP proxy URL
    - HTTPS_PROXY: HTTPS proxy URL

    Args:
        start: Starting path for finding .env file and project root.

    Returns:
        Configuration dictionary with headers, proxies, and token settings.
    """
    # Find and load .env file
    start_path = Path(start) if start else Path(__file__).parent.parent.parent
    project_root = find_project_root(start_path)
    env_file = project_root / ".env"

    if env_file.exists():
        load_dotenv(env_file)

    # Build configuration from environment variables
    config = {
        "headers": {
            "Accept-Language": os.getenv("ACCEPT_LANGUAGE", "zh-CN,zh;q=0.8,en-US;q=0.3,en;q=0.2"),
            "User-Agent": os.getenv(
                "USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            ),
            "Referer": os.getenv("REFERER", "https://www.douyin.com/"),
            "Cookie": os.getenv("COOKIE", ""),
        },
        "proxies": {
            "http": os.getenv("HTTP_PROXY") or None,
            "https": os.getenv("HTTPS_PROXY") or None,
        },
        "ms_token": {
            "url": os.getenv("MS_TOKEN_URL", "https://mssdk.bytedance.com/web/report"),
            "magic": os.getenv("MS_TOKEN_MAGIC", "538969122"),
            "version": os.getenv("MS_TOKEN_VERSION", "1"),
            "dataType": int(os.getenv("MS_TOKEN_DATATYPE", "8")),
            "strData": os.getenv("MS_TOKEN_STRDATA", ""),
            "User-Agent": os.getenv("MS_TOKEN_USER_AGENT", "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"),
        },
        "ttwid": {
            "url": os.getenv("TTWID_URL", "https://ttwid.bytedance.com/ttwid/union/register/"),
            "data": os.getenv(
                "TTWID_DATA",
                '{"region":"cn","aid":1768,"needFid":false,"service":"www.ixigua.com","migrate_info":{"ticket":"","source":"node"},"cbUrlProtocol":"https","union":true}',
            ),
        },
    }

    return config
