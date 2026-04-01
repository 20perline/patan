"""通用视频下载服务."""

import asyncio
import hashlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import httpx
from rich.progress import BarColumn, DownloadColumn, Progress, TaskID, TextColumn, TimeElapsedColumn, TimeRemainingColumn, TransferSpeedColumn

from patan.core.logging import get_console, get_logger
from patan.utils import sanitize_filename_text

logger = get_logger(__name__)


@dataclass(slots=True)
class DownloadJobResult:
    index: int
    value: Path | Exception


class DownloadProgressDisplay:
    """基于 rich 的终端多任务下载进度显示器。"""

    def __init__(
        self,
        *,
        refresh_interval: float = 0.1,
    ) -> None:
        self.console = get_console()
        self.enabled = self.console.is_terminal
        self._lock = asyncio.Lock()
        self._task_map: dict[int, TaskID] = {}
        self._progress = Progress(
            TextColumn("[bold blue]{task.fields[prefix]}[/]"),
            TextColumn("{task.description}", justify="left"),
            BarColumn(bar_width=None),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
            refresh_per_second=max(int(1 / refresh_interval), 1),
            disable=not self.enabled,
        )
        self._started = False
        self._closed = False

    async def add(self, task_id: int, description: str) -> None:
        async with self._lock:
            if task_id in self._task_map:
                return

            self._ensure_started()
            rich_task_id = self._progress.add_task(
                description,
                total=None,
                completed=0,
                prefix="WAIT",
            )
            self._task_map[task_id] = rich_task_id

    async def contains(self, task_id: int) -> bool:
        async with self._lock:
            return task_id in self._task_map

    async def update(self, task_id: int, downloaded: int, total: int) -> None:
        async with self._lock:
            rich_task_id = self._task_map.get(task_id)
            if rich_task_id is None:
                return

            if total > 0:
                self._progress.update(rich_task_id, completed=downloaded, total=total, prefix="DOWN")
            else:
                self._progress.update(rich_task_id, completed=downloaded, prefix="DOWN")

    async def mark_done(self, task_id: int) -> None:
        async with self._lock:
            rich_task_id = self._task_map.get(task_id)
            if rich_task_id is None:
                return

            task = self._progress.tasks[rich_task_id]
            total = task.total if task.total is not None else task.completed
            self._progress.update(
                rich_task_id,
                total=total,
                completed=total,
                prefix="DONE",
            )

    async def mark_failed(self, task_id: int, error: str) -> None:
        async with self._lock:
            rich_task_id = self._task_map.get(task_id)
            if rich_task_id is None:
                return

            task = self._progress.tasks[rich_task_id]
            description = str(task.description)
            failed_description = f"{description} [red]({error})[/red]"
            self._progress.update(rich_task_id, description=failed_description, prefix="FAIL")

    async def close(self) -> None:
        async with self._lock:
            if self._closed:
                return
            if self._started:
                self._progress.stop()
            self._closed = True

    def _ensure_started(self) -> None:
        if not self._started:
            self._progress.start()
            self._started = True


@dataclass(slots=True)
class DownloadContext:
    progress: DownloadProgressDisplay
    task_id: int
    owns_progress: bool


@dataclass(slots=True)
class BatchDownloadContext:
    progress: DownloadProgressDisplay
    job_queue: asyncio.Queue[tuple[int, str] | None]
    worker_count: int


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
        self._client: httpx.AsyncClient | None = None
        self._client_lock = asyncio.Lock()

    async def download(
        self,
        url: str,
        save_path: Path | str,
        filename: str | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        progress: DownloadProgressDisplay | None = None,
        task_id: int = 0,
    ) -> Path:
        """下载单个视频文件.

        Args:
            url: 视频 URL
            save_path: 保存目录
            filename: 文件名（可选，从 URL 推断）
            progress_callback: 进度回调函数 (downloaded, total)
            progress: 可选的共享进度显示器
            task_id: 当前下载任务对应的进度 ID

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

        logger.info("开始下载: %s", url)
        logger.info("保存到: %s", target_file)

        context = await self._prepare_download_context(
            progress=progress,
            task_id=task_id,
            description=target_file.name,
        )

        try:
            path = await self._download_to_file(
                url=url,
                target_file=target_file,
                progress=context.progress,
                task_id=context.task_id,
                progress_callback=progress_callback,
            )
            logger.info("下载完成: %s", target_file)
            await context.progress.mark_done(context.task_id)
            return path
        except Exception as exc:
            await self._fail_download(context, exc)
            raise
        finally:
            await self._close_download_context(context)

    async def close(self) -> None:
        """关闭复用的 HTTP client。"""
        async with self._client_lock:
            if self._client is None:
                return
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "VideoDownloader":
        """异步上下文入口。"""
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文出口。"""
        await self.close()

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
        results = []
        if not urls:
            return results

        context = await self._prepare_batch_context(urls)
        completed: list[DownloadJobResult] = []
        workers = self._create_batch_workers(
            context=context,
            total=len(urls),
            completed=completed,
            save_dir=save_dir,
            naming_template=naming_template,
            progress_callback=progress_callback,
        )
        await self._run_batch_workers(context, workers)

        for item in sorted(completed, key=lambda result: result.index):
            if isinstance(item.value, Exception):
                logger.error("任务 [%s] 失败: %s", item.index, item.value)
            else:
                results.append(item.value)
                logger.info("任务 [%s] 完成: %s", item.index, item.value)

        logger.info("批量下载完成: %s/%s，并发=%s", len(results), len(urls), context.worker_count)
        return results

    async def _run_download_job(
        self,
        *,
        index: int,
        url: str,
        save_dir: Path | str,
        naming_template: str,
        progress: DownloadProgressDisplay,
        progress_callback: Callable[[str, int, int], None] | None,
    ) -> DownloadJobResult:
        filename = self._generate_filename(naming_template, index, url)

        try:
            path = await self.download(
                url,
                save_dir,
                filename,
                (lambda downloaded, total: progress_callback(filename, downloaded, total)) if progress_callback else None,
                progress=progress,
                task_id=index,
            )
        except Exception as exc:
            return DownloadJobResult(index=index, value=exc)

        return DownloadJobResult(index=index, value=path)

    async def _prepare_batch_context(self, urls: list[str]) -> BatchDownloadContext:
        job_queue: asyncio.Queue[tuple[int, str] | None] = asyncio.Queue()
        worker_count = min(self.max_concurrent, len(urls))
        for index, url in enumerate(urls):
            await job_queue.put((index, url))
        for _ in range(worker_count):
            await job_queue.put(None)

        return BatchDownloadContext(
            progress=DownloadProgressDisplay(),
            job_queue=job_queue,
            worker_count=worker_count,
        )

    def _create_batch_workers(
        self,
        *,
        context: BatchDownloadContext,
        total: int,
        completed: list[DownloadJobResult],
        save_dir: Path | str,
        naming_template: str,
        progress_callback: Callable[[str, int, int], None] | None,
    ) -> list[asyncio.Task[None]]:
        return [
            asyncio.create_task(
                self._run_batch_worker(
                    worker_id=worker_id,
                    total=total,
                    context=context,
                    completed=completed,
                    save_dir=save_dir,
                    naming_template=naming_template,
                    progress_callback=progress_callback,
                )
            )
            for worker_id in range(context.worker_count)
        ]

    async def _run_batch_worker(
        self,
        *,
        worker_id: int,
        total: int,
        context: BatchDownloadContext,
        completed: list[DownloadJobResult],
        save_dir: Path | str,
        naming_template: str,
        progress_callback: Callable[[str, int, int], None] | None,
    ) -> None:
        while True:
            item = await context.job_queue.get()
            if item is None:
                context.job_queue.task_done()
                break

            index, url = item
            result = await self._run_download_job(
                index=index,
                url=url,
                save_dir=save_dir,
                naming_template=naming_template,
                progress=context.progress,
                progress_callback=progress_callback,
            )
            completed.append(result)
            self._log_worker_result(worker_id=worker_id, total=total, result=result)
            context.job_queue.task_done()

    async def _run_batch_workers(
        self,
        context: BatchDownloadContext,
        workers: list[asyncio.Task[None]],
    ) -> None:
        try:
            await context.job_queue.join()
            await asyncio.gather(*workers)
        finally:
            await context.progress.close()

    def _log_worker_result(
        self,
        *,
        worker_id: int,
        total: int,
        result: DownloadJobResult,
    ) -> None:
        if isinstance(result.value, Exception):
            logger.error("下载失败 [%s/%s] worker=%s: %s", result.index + 1, total, worker_id, result.value)
            return

        logger.info("下载任务完成 [%s/%s] worker=%s path=%s", result.index + 1, total, worker_id, result.value)

    async def _prepare_download_context(
        self,
        *,
        progress: DownloadProgressDisplay | None,
        task_id: int,
        description: str,
    ) -> DownloadContext:
        resolved_progress = progress or DownloadProgressDisplay()
        if not await resolved_progress.contains(task_id):
            await resolved_progress.add(task_id, description)
        return DownloadContext(
            progress=resolved_progress,
            task_id=task_id,
            owns_progress=progress is None,
        )

    async def _download_to_file(
        self,
        *,
        url: str,
        target_file: Path,
        progress: DownloadProgressDisplay,
        task_id: int,
        progress_callback: Callable[[int, int], None] | None,
    ) -> Path:
        try:
            client = await self._get_client()
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                total_size = int(response.headers.get("content-length", 0))
                await self._write_response_content(
                    response=response,
                    target_file=target_file,
                    progress=progress,
                    task_id=task_id,
                    total_size=total_size,
                    progress_callback=progress_callback,
                )
        except httpx.HTTPError as exc:
            logger.error("下载失败: %s", exc)
            raise OSError(f"Failed to download {url}: {exc}") from exc
        except OSError as exc:
            logger.error("保存失败: %s", exc)
            raise

        return target_file

    async def _get_client(self) -> httpx.AsyncClient:
        async with self._client_lock:
            if self._client is None:
                self._client = httpx.AsyncClient(
                    proxy=self.proxy,
                    timeout=httpx.Timeout(self.timeout),
                    limits=httpx.Limits(max_connections=self.max_concurrent),
                    follow_redirects=True,
                )
            return self._client

    async def _write_response_content(
        self,
        *,
        response: httpx.Response,
        target_file: Path,
        progress: DownloadProgressDisplay,
        task_id: int,
        total_size: int,
        progress_callback: Callable[[int, int], None] | None,
    ) -> None:
        downloaded = 0
        with target_file.open("wb") as f:
            async for chunk in response.aiter_bytes(self.chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                await progress.update(task_id, downloaded, total_size)
                if progress_callback:
                    progress_callback(downloaded, total_size)

    async def _fail_download(self, context: DownloadContext, exc: Exception) -> None:
        await context.progress.mark_failed(context.task_id, str(exc))

    async def _close_download_context(self, context: DownloadContext) -> None:
        if context.owns_progress:
            await context.progress.close()

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


class DownloadProgressLogger:
    """下载进度追踪器."""

    def __init__(self, description: str = "下载中") -> None:
        self.description = description
        self.last_print_time = 0
        self.print_interval = 1.0  # 秒

    def __call__(self, downloaded: int, total: int) -> None:
        """作为进度回调使用."""
        current_time = time.time()
        if current_time - self.last_print_time < self.print_interval:
            return

        self.last_print_time = current_time

        if total > 0:
            percent = (downloaded / total) * 100
            logger.info("%s: %.1f%% (%s/%s)", self.description, percent, downloaded, total)
        else:
            logger.info("%s: %s bytes", self.description, downloaded)
