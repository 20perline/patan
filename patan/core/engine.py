# _*_ coding: utf-8 _*_

import logging
import asyncio
from .scheduler import Scheduler
from .downloader import Downloader
from ..http import Request
from ..spiders import BaseSpider

logger = logging.getLogger(__name__)

class Engine(object):

    def __init__(self, spider=None, loop=None, downloader=None, worker_num=20):
        self.loop = loop or asyncio.get_event_loop()
        self.scheduler = Scheduler(loop=self.loop)
        self.spider = spider or BaseSpider()
        self.downloader = downloader or Downloader(self.loop)
        self.worker_num = worker_num

    async def schedule(self, request: Request):
        await self.scheduler.enqueue(request)

    async def work(self):
        fetch_tasks = [asyncio.Task(self.fetch(i), loop=self.loop) for i in range(self.worker_num)]
        await self.scheduler.join()
        for task in fetch_tasks:
            task.cancel()
        return

    async def fetch(self, worker_id):
        try:
            while True:
                request = await self.scheduler.dequeue()
                logger.debug('[Worker{}] fetching {}'.format(worker_id, request.url))
                response = await self.downloader.fetch(request, self.spider)
                for result in request.callback(response):
                    await self.schedule(result)
                self.scheduler.formerly_done()
        except asyncio.CancelledError:
            pass
        return

    def start(self):
        for req in self.spider.start_requests():
            self.scheduler.enqueue_nowait(req)
        try:
            self.loop.run_until_complete(self.work())
        except KeyboardInterrupt as e:
            logger.warning("%s KeyboardInterrupt: force stopped", e)
        finally:
            self.loop.stop()
            self.loop.run_forever()
            self.loop.close()
            self.downloader.close()