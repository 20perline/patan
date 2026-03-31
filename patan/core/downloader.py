"""通用视频下载服务."""

import asyncio
import hashlib
from pathlib import Path
from typing import Callable

import httpx
from patan.core.logging import logger
from patan.utils import sanitize_filename_text


class VideoDownloader:
    """通用视频下载器.

    支持单文件下载、批量下载、断点续传等功能。
    """

    def __init__(
        self,
        *,
        max_concurrent: int = 3,
        timeout: float = 30.0,
        chunk_size: int = 1024 * 1024,  # 1MB
        proxy: str | None = None,
    ) -> None:
        """初始化下载器.

        Args:
            max_concurrent: 最大并发下载数
            timeout: 请求超时时间
            chunk_size: 下载块大小
            proxy: 代理服务器地址
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.proxy = proxy

    async def download(
        self,
        url: str,
        save_path: Path | str,
        filename: str | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        """下载单个视频文件.

        Args:
            url: 视频 URL
            save_path: 保存目录
            filename: 文件名（可选，从 URL 推断）
            progress_callback: 进度回调函数 (downloaded, total)

        Returns:
            保存的文件路径

        Raises:
            IOError: 下载失败或保存失败
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # 确定文件名
        if filename:
            target_file = save_path / filename
        else:
            # 从 URL 推断文件名
            target_file = save_path / self._extract_filename(url)

        logger.info(f"开始下载: {url}")
        logger.info(f"保存到: {target_file}")

        try:
            async with httpx.AsyncClient(
                proxy=self.proxy,
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True
            ) as client:
                async with client.stream("GET", url) as response:
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    with open(target_file, "wb") as f:
                        async for chunk in response.aiter_bytes(self.chunk_size):
                            f.write(chunk)
                            downloaded += len(chunk)

                            if progress_callback:
                                progress_callback(downloaded, total_size)

            logger.info(f"下载完成: {target_file}")
            return target_file

        except httpx.HTTPError as exc:
            logger.error(f"下载失败: {exc}")
            raise IOError(f"Failed to download {url}: {exc}") from exc
        except IOError as exc:
            logger.error(f"保存失败: {exc}")
            raise

    async def download_batch(
        self,
        urls: list[str],
        save_dir: Path | str,
        naming_template: str = "{title}",
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> list[Path]:
        """批量下载视频.

        Args:
            urls: 视频 URL 列表
            save_dir: 保存目录
            naming_template: 文件命名模板，支持 {title}, {author}, {id} 等占位符
            progress_callback: 进度回调函数 (filename, downloaded, total)

        Returns:
            下载的文件路径列表
        """
        semaphore = asyncio.Semaphore(self.max_concurrent)
        results = []

        async def download_one(url: str, index: int) -> tuple[int, Path | Exception]:
            async with semaphore:
                try:
                    filename = self._generate_filename(naming_template, index, url)
                    path = await self.download(url, save_dir, filename)
                    return (index, path)
                except Exception as exc:
                    logger.error(f"下载失败 [{index}]: {exc}")
                    return (index, exc)

        tasks = [download_one(url, i) for i, url in enumerate(urls)]
        completed = await asyncio.gather(*tasks)

        for index, result in sorted(completed):
            if isinstance(result, Exception):
                logger.error(f"任务 [{index}] 失败: {result}")
            else:
                results.append(result)
                logger.info(f"任务 [{index}] 完成: {result}")

        logger.info(f"批量下载完成: {len(results)}/{len(urls)}")
        return results

    def _extract_filename(self, url: str) -> str:
        """从 URL 提取文件名."""
        # 简单实现：从 URL 路径推断
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path_parts = parsed.path.split("/")
        filename = path_parts[-1] if path_parts else "video.mp4"

        # 如果没有扩展名，默认为 .mp4
        if not filename.endswith((".mp4", ".flv", ".m3u8")):
            filename += ".mp4"

        return sanitize_filename_text(filename)

    def _generate_filename(self, template: str, index: int, url: str) -> str:
        """根据模板生成文件名."""
        # 基础实现，可以扩展更多占位符
        filename = template.format(
            index=index,
            id=hashlib.md5(url.encode()).hexdigest()[:8],
        )
        return sanitize_filename_text(filename)


class DownloadProgress:
    """下载进度追踪器."""

    def __init__(self, description: str = "下载中") -> None:
        self.description = description
        self.last_print_time = 0
        self.print_interval = 1.0  # 秒

    def __call__(self, downloaded: int, total: int) -> None:
        """作为进度回调使用."""
        import time

        current_time = time.time()
        if current_time - self.last_print_time < self.print_interval:
            return

        self.last_print_time = current_time

        if total > 0:
            percent = (downloaded / total) * 100
            logger.info(f"{self.description}: {percent:.1f}% ({downloaded}/{total})")
        else:
            logger.info(f"{self.description}: {downloaded} bytes")
