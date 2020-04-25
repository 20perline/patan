# _*_ coding: utf-8 _*_

import logging
import asyncio
from .scheduler import Scheduler
from .downloader import Downloader
from .spiders import BaseSpider
from .request import Request

logger = logging.getLogger(__name__)


class Engine(object):

    def __init__(self, spider=None, downloader=None, worker_num=20):
        self.scheduler = Scheduler()
        self.spider = spider or BaseSpider()
        self.downloader = downloader or Downloader()
        self.worker_num = worker_num

    async def bootstrap(self):
        for req in self.spider.start_requests():
            self.scheduler.enqueue_nowait(req)

        workers = [asyncio.create_task(self.work(), name='Task-{:0>2d}'.format(_)) for _ in range(self.worker_num)]
        # Wait until the queue is fully processed.
        await self.scheduler.start()

        await asyncio.gather(*workers, return_exceptions=True)

        await self.shutdown()

    async def shutdown(self):
        await self.spider.close()
        await self.downloader.close()
        logger.info('engine is shutdown.')

    async def work(self):
        while True:
            request = await self.scheduler.dequeue()
            response = await self.downloader.fetch(request)
            self.scheduler.complete_request()
            if response is None or response.text is None:
                continue
            async for result in request.callback(response):
                if isinstance(result, Request):
                    await self.scheduler.enqueue(result)

    def start(self):
        asyncio.run(self.bootstrap(), debug=False)
