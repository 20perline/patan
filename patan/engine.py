# _*_ coding: utf-8 _*_

import logging
import asyncio
from .scheduler import Scheduler
from .spiders import BaseSpider

logger = logging.getLogger(__name__)


class Engine(object):

    def __init__(self, spider=None, worker_num=20):
        self.worker_num = worker_num
        self.scheduler = Scheduler(worker_num)
        self.spider = spider or BaseSpider()

    async def bootstrap(self):
        for req in self.spider.start_requests():
            self.scheduler.enqueue_nowait(req)
        try:
            await self.scheduler.start()
        finally:
            await self.shutdown()

    async def shutdown(self):
        try:
            await self.spider.close()
        except Exception as e:
            logger.warn('failed to close the spider: %s' % str(e))
        finally:
            pass

    def start(self):
        asyncio.run(self.bootstrap(), debug=False)
        logger.info('engine is shutdown now')
