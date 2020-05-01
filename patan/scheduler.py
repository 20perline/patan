# _*_ coding: utf-8 _*_

import logging
import asyncio
from .request import Request
from .filters import SimpleDupFilter

logger = logging.getLogger(__name__)


class Scheduler(object):

    def __init__(self, dup_filter=None):
        self.queue = None
        self.df = dup_filter or SimpleDupFilter()

    def ensure_queue(self):
        if self.queue is None:
            self.queue = asyncio.Queue(1024)

    # push new request to the queue immediately, won't block
    def enqueue_nowait(self, request: Request):
        self.ensure_queue()
        if not self.df.seen(request):
            self.queue.put_nowait(request)

    # push new request to the queue, will block if need
    async def enqueue(self, request: Request):
        self.ensure_queue()
        if not self.df.seen(request):
            await self.queue.put(request)

    # pop new request from the queue, will block if need
    async def dequeue(self):
        self.ensure_queue()
        request = await self.queue.get()
        return request

    # confirm that last task is done
    def acknowledge(self):
        self.queue.task_done()

    # join queue
    async def start(self):
        self.ensure_queue()
        await self.queue.join()

    def is_idle(self):
        return self.queue.empty()
