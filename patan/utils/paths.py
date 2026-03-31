import sys
from pathlib import Path


def ensure_path(path: str | Path) -> Path:
    return path if isinstance(path, Path) else Path(path)


def split_filename(text: str, os_limit: dict[str, int]) -> str:
    limit = os_limit.get(sys.platform, 200)
    chinese_length = sum(1 for char in text if "\u4e00" <= char <= "\u9fff") * 3
    english_length = sum(1 for char in text if char.isalpha())
    total_length = chinese_length + english_length + text.count("_")
    if total_length <= limit:
        return text
    split_index = min(total_length, limit) // 2 - 6
    return text[:split_index] + "......" + text[-split_index:]
