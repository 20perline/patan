"""通用去重服务."""

import hashlib
from pathlib import Path
from typing import Any, Callable

from patan.core.logging import logger


class ContentDeduplicator:
    """内容去重器.

    基于内容特征进行去重，支持多种去重策略。
    """

    def __init__(
        self,
        strategy: str = "content_hash",  # content_hash, file_hash, custom
    ) -> None:
        """初始化去重器.

        Args:
            strategy: 去重策略
                - content_hash: 基于内容哈希
                - file_hash: 基于文件哈希
                - custom: 自定义去重逻辑
        """
        self.strategy = strategy
        self._seen_hashes: set[str] = set()
        self._custom_checkers: dict[str, Callable[[Any], str]] = {}

    def is_duplicate(self, item: Any) -> bool:
        """检查项目是否重复.

        Args:
            item: 要检查的项目

        Returns:
            True 如果重复，False 如果是新项目
        """
        if self.strategy == "custom":
            # 使用自定义检查器
            for checker_name, checker_func in self._custom_checkers.items():
                try:
                    hash_value = checker_func(item)
                    if hash_value in self._seen_hashes:
                        logger.debug(f"重复内容 ({checker_name}): {hash_value}")
                        return True
                except Exception as exc:
                    logger.warning(f"自定义检查器 {checker_name} 失败: {exc}")

        return False

    def mark_seen(self, item: Any) -> None:
        """标记项目为已 seen.

        Args:
            item: 要标记的项目
        """
        hash_value = self._compute_hash(item)
        if hash_value:
            self._seen_hashes.add(hash_value)
            logger.debug(f"标记已 seen: {hash_value}")

    def _compute_hash(self, item: Any) -> str | None:
        """计算项目的哈希值.

        Args:
            item: 要计算哈希的项目

        Returns:
            哈希字符串，如果无法计算则返回 None
        """
        if self.strategy == "content_hash":
            if isinstance(item, (str, bytes)):
                return hashlib.md5(str(item).encode()).hexdigest()
            elif isinstance(item, dict):
                # 对于字典，使用排序后的值计算哈希
                sorted_items = sorted(item.items())
                return hashlib.md5(str(sorted_items).encode()).hexdigest()
            elif isinstance(item, Path):
                # 对于文件，计算文件哈希
                if item.exists():
                    return self._file_hash(item)
        elif self.strategy == "file_hash":
            if isinstance(item, Path):
                return self._file_hash(item)

        return None

    def _file_hash(self, file_path: Path) -> str | None:
        """计算文件哈希.

        Args:
            file_path: 文件路径

        Returns:
            文件的 MD5 哈希值
        """
        try:
            md5_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except (IOError, OSError) as exc:
            logger.error(f"无法计算文件哈希 {file_path}: {exc}")
            return None

    def register_custom_checker(self, name: str, checker: Callable[[Any], str]) -> None:
        """注册自定义去重检查器.

        Args:
            name: 检查器名称
            checker: 检查函数，接收项目，返回哈希字符串
        """
        self._custom_checkers[name] = checker
        logger.info(f"注册自定义检查器: {name}")

    def clear(self) -> None:
        """清空已 seen 的记录."""
        self._seen_hashes.clear()
        logger.info("去重记录已清空")

    @property
    def seen_count(self) -> int:
        """获取已 seen 的项目数量."""
        return len(self._seen_hashes)


class URLDeduplicator(ContentDeduplicator):
    """URL 去重器."""

    def __init__(self) -> None:
        super().__init__(strategy="content_hash")

    def is_duplicate_url(self, url: str) -> bool:
        """检查 URL 是否重复.

        Args:
            url: 要检查的 URL

        Returns:
            True 如果重复，False 如果是新 URL
        """
        return self.is_duplicate(url)

    def mark_url_seen(self, url: str) -> None:
        """标记 URL 为已 seen.

        Args:
            url: URL 字符串
        """
        self.mark_seen(url)


class MetadataDeduplicator(ContentDeduplicator):
    """元数据去重器."""

    def __init__(self) -> None:
        super().__init__(strategy="content_hash")

        # 注册基于关键字的去重检查器
        self.register_custom_checker("title", lambda item: item.get("title", ""))
        self.register_custom_checker("author_id", lambda item: item.get("author_id", ""))
        self.register_custom_checker("unique_id", lambda item: item.get("extra", {}).get("aweme_id", ""))
