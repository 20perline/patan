"""通用任务调度器.

支持任务队列、限流、并发控制、失败重试等功能。
"""

import asyncio
import time
from collections import deque
from typing import Any, Callable, TypeVar

from patan.core.logging import logger

T = TypeVar("T")


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
        func: Callable[..., T],
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
                    logger.debug(f"执行任务: {func.__name__} (尝试 {attempt + 1}/{self.max_retries + 1})")
                    result = await func(*args, **kwargs)
                    return result

            except Exception as exc:
                last_exception = exc
                logger.warning(f"任务失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {exc}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)

        # 所有重试都失败了
        logger.error(f"任务执行失败: {func.__name__}")
        raise last_exception or Exception("Task execution failed")

    async def run_batch(
        self,
        func: Callable[..., T],
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
        completed = 0
        failed = 0
        results = []

        async def run_one(args: tuple) -> tuple[int, T | Exception]:
            nonlocal completed, failed

            try:
                result = await self.run_task(func, *args)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, failed)
                return (len(results), result)
            except Exception as exc:
                failed += 1
                if progress_callback:
                    progress_callback(completed, total, failed)
                return (len(results), exc)

        tasks = [run_one(args) for args in args_list]
        task_results = await asyncio.gather(*tasks)

        for index, result in sorted(task_results):
            if isinstance(result, Exception):
                logger.error(f"批量任务 [{index}] 失败: {result}")
            else:
                results.append(result)

        logger.info(f"批量任务完成: 成功 {completed}/{total}, 失败 {failed}/{total}")
        return results

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
        logger.debug(f"任务已加入队列: {func.__name__}, 队列长度: {len(self._queue)}")

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
        completed = 0
        results = []

        logger.info(f"开始执行 {total_tasks} 个任务")

        while self._queue:
            func, args, kwargs = self._queue.popleft()
            try:
                result = await self.scheduler.run_task(func, *args, **kwargs)
                results.append(result)
                completed += 1
                logger.info(f"任务进度: {completed}/{total_tasks}")
            except Exception as exc:
                logger.error(f"任务执行失败: {func.__name__}: {exc}")
                self._running = False
                raise

        self._running = False
        logger.info(f"所有任务完成: {completed}/{total_tasks}")
        return results

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
