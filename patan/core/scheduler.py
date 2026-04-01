"""通用任务调度器.

支持任务队列、限流、并发控制、失败重试等功能。
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from patan.core.logging import get_logger

T = TypeVar("T")
logger = get_logger(__name__)


@dataclass(slots=True)
class TaskResult:
    index: int
    value: Any | Exception


@dataclass(slots=True)
class BatchRunContext:
    queue: asyncio.Queue[tuple[int, tuple[Any, ...]] | None]
    worker_count: int


@dataclass(slots=True)
class QueueRunContext:
    queue: asyncio.Queue[tuple[int, Callable[..., Awaitable[Any]], tuple[Any, ...], dict[str, Any]] | None]
    worker_count: int


class TaskScheduler:
    """通用任务调度器."""

    def __init__(
        self,
        *,
        max_concurrent: int = 5,
        rate_limit: float = 1.0,  # 每秒最多请求数
        max_retries: int = 3,
        retry_delay: float = 5.0,
    ) -> None:
        """初始化任务调度器.

        Args:
            max_concurrent: 最大并发任务数
            rate_limit: 速率限制（请求/秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._request_times: deque[float] = deque()

    async def run_task(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """运行单个任务，支持重试和限流。

        Args:
            func: 异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 任务执行失败且重试次数用尽
        """
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # 限流控制
                await self._rate_limit_wait()

                # 并发控制
                async with self._semaphore:
                    logger.debug("执行任务: %s (尝试 %s/%s)", func.__name__, attempt + 1, self.max_retries + 1)
                    result = await func(*args, **kwargs)
                    return result

            except Exception as exc:
                last_exception = exc
                logger.warning("任务失败 (尝试 %s/%s): %s", attempt + 1, self.max_retries + 1, exc)

                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)

        # 所有重试都失败了
        logger.error("任务执行失败: %s", func.__name__)
        raise last_exception or Exception("Task execution failed")

    async def run_batch(
        self,
        func: Callable[..., Awaitable[T]],
        args_list: list[tuple[Any, ...]],
        progress_callback: Callable[[int, int, int], None] | None = None,
    ) -> list[T]:
        """批量运行任务.

        Args:
            func: 异步函数
            args_list: 函数参数列表，每个元素是一个参数元组
            progress_callback: 进度回调 (completed, total, failed)

        Returns:
            执行结果列表
        """
        total = len(args_list)
        if total == 0:
            return []

        completed = 0
        failed = 0
        results: list[TaskResult] = []
        context = await self._prepare_batch_run_context(args_list)
        counters = {"completed": completed, "failed": failed}
        workers = self._create_batch_workers(
            func=func,
            total=total,
            context=context,
            results=results,
            counters=counters,
            progress_callback=progress_callback,
        )
        await self._run_batch_workers(context, workers)

        completed = counters["completed"]
        failed = counters["failed"]
        logger.info("批量任务完成: 成功 %s/%s, 失败 %s/%s，并发=%s", completed, total, failed, total, context.worker_count)
        return [item.value for item in sorted(results, key=lambda item: item.index) if not isinstance(item.value, Exception)]

    async def _run_batch_item(
        self,
        func: Callable[..., Awaitable[T]],
        index: int,
        args: tuple[Any, ...],
    ) -> TaskResult:
        try:
            return TaskResult(index=index, value=await self.run_task(func, *args))
        except Exception as exc:
            return TaskResult(index=index, value=exc)

    async def _prepare_batch_run_context(self, args_list: list[tuple[Any, ...]]) -> BatchRunContext:
        queue: asyncio.Queue[tuple[int, tuple[Any, ...]] | None] = asyncio.Queue()
        worker_count = min(self.max_concurrent, len(args_list))
        for index, args in enumerate(args_list):
            await queue.put((index, args))
        for _ in range(worker_count):
            await queue.put(None)
        return BatchRunContext(queue=queue, worker_count=worker_count)

    def _create_batch_workers(
        self,
        *,
        func: Callable[..., Awaitable[T]],
        total: int,
        context: BatchRunContext,
        results: list[TaskResult],
        counters: dict[str, int],
        progress_callback: Callable[[int, int, int], None] | None,
    ) -> list[asyncio.Task[None]]:
        return [
            asyncio.create_task(
                self._run_batch_worker(
                    worker_id=worker_id,
                    func=func,
                    total=total,
                    context=context,
                    results=results,
                    counters=counters,
                    progress_callback=progress_callback,
                )
            )
            for worker_id in range(context.worker_count)
        ]

    async def _run_batch_worker(
        self,
        *,
        worker_id: int,
        func: Callable[..., Awaitable[T]],
        total: int,
        context: BatchRunContext,
        results: list[TaskResult],
        counters: dict[str, int],
        progress_callback: Callable[[int, int, int], None] | None,
    ) -> None:
        while True:
            item = await context.queue.get()
            if item is None:
                context.queue.task_done()
                break

            index, args = item
            result = await self._run_batch_item(func, index, args)
            results.append(result)
            self._update_batch_counters(worker_id, total, result, counters)
            if progress_callback:
                progress_callback(counters["completed"], total, counters["failed"])
            context.queue.task_done()

    async def _run_batch_workers(
        self,
        context: BatchRunContext,
        workers: list[asyncio.Task[None]],
    ) -> None:
        await context.queue.join()
        await asyncio.gather(*workers)

    def _update_batch_counters(
        self,
        worker_id: int,
        total: int,
        result: TaskResult,
        counters: dict[str, int],
    ) -> None:
        if isinstance(result.value, Exception):
            counters["failed"] += 1
            logger.error("批量任务 [%s] 失败: %s", result.index, result.value)
            return

        counters["completed"] += 1
        logger.debug("批量任务完成 [%s/%s] worker=%s", result.index + 1, total, worker_id)

    async def _rate_limit_wait(self) -> None:
        """等待以符合速率限制."""
        current_time = time.time()

        # 移除过期的请求时间记录
        while self._request_times and current_time - self._request_times[0] > 1.0:
            self._request_times.popleft()

        # 如果达到速率限制，等待
        if len(self._request_times) >= self.rate_limit:
            sleep_time = 1.0 - (current_time - self._request_times[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

        # 记录本次请求时间
        self._request_times.append(time.time())


class AsyncTaskQueue:
    """异步任务队列."""

    def __init__(self, scheduler: TaskScheduler) -> None:
        """初始化任务队列.

        Args:
            scheduler: 任务调度器实例
        """
        self.scheduler = scheduler
        self._queue: deque[tuple[Callable, tuple, dict]] = deque()
        self._running = False

    def add_task(self, func: Callable, *args: Any, **kwargs: Any) -> None:
        """添加任务到队列.

        Args:
            func: 异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        """
        self._queue.append((func, args, kwargs))
        logger.debug("任务已加入队列: %s, 队列长度: %s", func.__name__, len(self._queue))

    async def run_all(self) -> list[Any]:
        """运行队列中的所有任务.

        Returns:
            执行结果列表

        Raises:
            Exception: 任一任务失败
        """
        if not self._queue:
            logger.info("任务队列为空")
            return []

        self._running = True
        total_tasks = len(self._queue)
        results: list[TaskResult] = []
        counters = {"completed": 0, "failed": 0}

        logger.info("开始执行 %s 个任务", total_tasks)
        context = await self._prepare_queue_run_context()
        workers = self._create_queue_workers(
            total_tasks=total_tasks,
            context=context,
            results=results,
            counters=counters,
        )
        await self._run_queue_workers(context, workers)

        self._running = False
        completed = counters["completed"]
        failed = counters["failed"]
        logger.info("所有任务完成: 成功 %s/%s, 失败 %s/%s", completed, total_tasks, failed, total_tasks)
        if failed:
            raise RuntimeError(f"{failed} task(s) failed in queue execution")
        return [item.value for item in sorted(results, key=lambda item: item.index) if not isinstance(item.value, Exception)]

    async def _run_queue_item(
        self,
        index: int,
        func: Callable,
        args: tuple,
        kwargs: dict,
    ) -> TaskResult:
        try:
            return TaskResult(index=index, value=await self.scheduler.run_task(func, *args, **kwargs))
        except Exception as exc:
            return TaskResult(index=index, value=exc)

    async def _prepare_queue_run_context(self) -> QueueRunContext:
        queue: asyncio.Queue[tuple[int, Callable[..., Awaitable[Any]], tuple[Any, ...], dict[str, Any]] | None] = asyncio.Queue()
        total_tasks = len(self._queue)
        worker_count = min(self.scheduler.max_concurrent, total_tasks)

        while self._queue:
            index = total_tasks - len(self._queue)
            func, args, kwargs = self._queue.popleft()
            await queue.put((index, func, args, kwargs))

        for _ in range(worker_count):
            await queue.put(None)

        return QueueRunContext(queue=queue, worker_count=worker_count)

    def _create_queue_workers(
        self,
        *,
        total_tasks: int,
        context: QueueRunContext,
        results: list[TaskResult],
        counters: dict[str, int],
    ) -> list[asyncio.Task[None]]:
        return [
            asyncio.create_task(
                self._run_queue_worker(
                    worker_id=worker_id,
                    total_tasks=total_tasks,
                    context=context,
                    results=results,
                    counters=counters,
                )
            )
            for worker_id in range(context.worker_count)
        ]

    async def _run_queue_worker(
        self,
        *,
        worker_id: int,
        total_tasks: int,
        context: QueueRunContext,
        results: list[TaskResult],
        counters: dict[str, int],
    ) -> None:
        while True:
            item = await context.queue.get()
            if item is None:
                context.queue.task_done()
                break

            index, func, args, kwargs = item
            result = await self._run_queue_item(index, func, args, kwargs)
            results.append(result)
            self._update_queue_counters(worker_id, total_tasks, func, result, counters)
            context.queue.task_done()

    async def _run_queue_workers(
        self,
        context: QueueRunContext,
        workers: list[asyncio.Task[None]],
    ) -> None:
        await context.queue.join()
        await asyncio.gather(*workers)

    def _update_queue_counters(
        self,
        worker_id: int,
        total_tasks: int,
        func: Callable[..., Awaitable[Any]],
        result: TaskResult,
        counters: dict[str, int],
    ) -> None:
        if isinstance(result.value, Exception):
            counters["failed"] += 1
            logger.error("任务执行失败: %s: %s", func.__name__, result.value)
            return

        counters["completed"] += 1
        logger.info("任务进度: %s/%s (worker=%s)", counters["completed"], total_tasks, worker_id)

    @property
    def is_running(self) -> bool:
        """检查队列是否正在运行."""
        return self._running

    @property
    def queue_size(self) -> int:
        """获取队列大小."""
        return len(self._queue)

    def clear(self) -> None:
        """清空任务队列."""
        self._queue.clear()
        logger.info("任务队列已清空")
