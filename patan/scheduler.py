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

    def enqueue_nowait(self, request: Request):
        self.ensure_queue()
        if not self.df.is_duplicated(request):
            self.queue.put_nowait(request)

    async def enqueue(self, request: Request):
        self.ensure_queue()
        if not self.df.is_duplicated(request):
            logger.debug('pushing new request {}'.format(request.url))
            await self.queue.put(request)

    async def dequeue(self):
        self.ensure_queue()
        task_name = asyncio.current_task().get_name()
        logger.info('%s is waiting for new request...' % (task_name))
        req = await self.queue.get()
        return req

    async def start(self):
        self.ensure_queue()
        await self.queue.join()

    def complete_request(self):
        self.queue.task_done()
