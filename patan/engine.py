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

        consumers = [asyncio.create_task(self.work(), name='Task-{:0>2d}'.format(_)) for _ in range(self.worker_num)]
        await asyncio.gather(*consumers)

        await self.scheduler.start()

    async def work(self):
        while True:
            request = await self.scheduler.dequeue()
            logger.info('>'*3 + ' ' + request.url)
            response = await self.downloader.fetch(request)
            if response is None or response.text is None:
                continue
            logger.info('<'*3 + ' ' + request.url)
            async for result in request.callback(response):
                if isinstance(result, Request):
                    await self.scheduler.enqueue(result)
                else:
                    logger.info('<'*6 + ' ' + result)
            self.scheduler.complete_request()

    def start(self):
        asyncio.run(self.bootstrap(), debug=False)
        print('end')
