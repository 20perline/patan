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
            self.queue = asyncio.Queue(1000)

    def enqueue_nowait(self, request: Request):
        self.ensure_queue()
        if not self.df.is_duplicated(request):
            self.queue.put_nowait(request)

    async def enqueue(self, request: Request):
        self.ensure_queue()
        if not self.df.is_duplicated(request):
            await self.queue.put(request)
        else:
            logger.debug('skipping {}'.format(request.url))

    async def dequeue(self):
        self.ensure_queue()
        req = await self.queue.get()
        return req

    async def start(self):
        self.ensure_queue()
        await self.queue.join()

    def complete_request(self):
        self.queue.task_done()
