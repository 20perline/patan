# _*_ coding: utf-8 _*_

import logging
import asyncio
from ..http import Request
from ..utils import SimpleDupFilter

logger = logging.getLogger(__name__)


class Scheduler(object):

    def __init__(self, dup_filter=None, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.queue = asyncio.Queue(loop=self.loop)
        self.df = dup_filter or SimpleDupFilter()

    def enqueue_nowait(self, request: Request):
        if not self.df.request_seen(request):
            self.queue.put_nowait(request)

    async def enqueue(self, request: Request):
        if not self.df.request_seen(request):
            await self.queue.put(request)

    async def dequeue(self):
        return await self.queue.get()

    async def join(self):
        await self.queue.join()

    def formerly_done(self):
        self.queue.task_done()
