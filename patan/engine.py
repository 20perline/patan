# _*_ coding: utf-8 _*_

import logging
import asyncio
from .request import Request
from .scheduler import Scheduler
from .spiders import BaseSpider
from .downloader import Downloader

logger = logging.getLogger(__name__)


class Engine(object):

    def __init__(self, spider=None, worker_num=20):
        self.worker_num = worker_num
        self.idle_worker_names = set()
        self.workers = []
        self.scheduler = Scheduler()
        self.downloader = Downloader()
        self.spider = spider or BaseSpider()

    async def bootstrap(self):
        for req in self.spider.start_requests():
            self.scheduler.enqueue_nowait(req)

        # create all workers and start concurrently
        for _ in range(self.worker_num):
            name = 'Task-{:0>2d}'.format(_)
            task = asyncio.create_task(self.work())
            task.set_name(name)
            self.workers.append(task)

        try:
            # start scheduler
            await self.scheduler.start()
            # start manager worker
            await asyncio.shield(self.manage())
            # start payload workers
            await asyncio.gather(*self.workers, return_exceptions=True)
        finally:
            await self.shutdown()

    # producer-consumer worker run in endless loop
    async def work(self):
        worker_name = asyncio.current_task().get_name()
        try:
            await self._work(worker_name)
        except asyncio.CancelledError:
            logger.info('worker %s is cancelled' % worker_name)
        except Exception as e:
            logger.info('worker %s is crushed, exception: %s' % (worker_name, str(e)))
        finally:
            await self.release()

    async def _work(self, worker_name):
        while True:
            logger.info('%s is waiting for new request...' % (worker_name))
            self.idle_worker_names.add(worker_name)
            request = await self.scheduler.dequeue()
            self.idle_worker_names.remove(worker_name)

            response = None
            try:
                response = await self.downloader.fetch(request)
            finally:
                self.scheduler.acknowledge()

            if response is None or response.text is None:
                continue
            async for result in request.callback(response):
                if isinstance(result, Request):
                    await self.scheduler.enqueue(result)

    # manager worker used to gracefully exit
    async def manage(self):
        while True:
            await asyncio.sleep(1)
            if len(self.workers) == 0:
                continue
            # when scheduler's queue is empty and all workers are idle
            # manager worker will terminate the engine
            if self.scheduler.is_idle() and len(self.idle_worker_names) == self.worker_num:
                for worker in self.workers:
                    worker.cancel()
                break

    # shutdown the engine and finalize resources
    async def shutdown(self):
        try:
            await self.downloader.close()
            await self.spider.close()
        except Exception as e:
            logger.warn('failed to close components: %s' % str(e))
        finally:
            logger.info('engine is shutdown now')

    def start(self):
        asyncio.run(self.bootstrap(), debug=False)
