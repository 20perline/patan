# _*_ coding: utf-8 _*_

import logging
import asyncio
from .request import Request
from .filters import SimpleDupFilter
from .downloader import Downloader
from .worker import Worker

logger = logging.getLogger(__name__)


class Scheduler(object):

    def __init__(self, worker_num, dup_filter=None):
        self.queue = None
        self.worker_num = worker_num
        self.workers = {}
        self.df = dup_filter or SimpleDupFilter()
        self.downloader = Downloader()

    def ensure_queue(self):
        if self.queue is None:
            self.queue = asyncio.Queue(1024)

    def enqueue_nowait(self, request: Request):
        self.ensure_queue()
        if not self.df.seen(request):
            self.queue.put_nowait(request)

    async def enqueue(self, request: Request):
        self.ensure_queue()
        if not self.df.seen(request):
            logger.debug('pushing new request {}'.format(request.url))
            await self.queue.put(request)

    async def dequeue(self):
        self.ensure_queue()
        worker_name = asyncio.current_task().get_name()
        self.worker_pause(worker_name)
        request = await self.queue.get()
        self.worker_resume(worker_name)
        return request

    def task_done(self):
        self.queue.task_done()

    def worker_pause(self, name):
        logger.info('%s is waiting for new request...' % (name))
        self.workers.get(name).status = 0

    def worker_resume(self, name):
        self.workers.get(name).status = 1

    # create all workers and start concurrently
    async def start(self):
        self.ensure_queue()

        wl = []
        for _ in range(self.worker_num):
            name = 'Task-{:0>2d}'.format(_)
            task = asyncio.create_task(self.work())
            task.set_name(name)
            worker = Worker(task, name, 1)
            self.workers.update({name: worker})
            wl.append(task)

        await self.queue.join()

        await asyncio.shield(self.manage())

        await asyncio.gather(*wl, return_exceptions=True)

    # attempt to cancel all the workers when they're all idle
    def attempt_to_stop(self):
        self.ensure_queue()
        if len(self.workers) == 0:
            return False
        if self.queue.empty() and 0 == sum(v.status for k, v in self.workers.items()):
            for name, worker in self.workers.items():
                worker.task.cancel()
            return True
        return False

    # producer-consumer worker run in endless loop
    async def work(self):
        worker_name = asyncio.current_task().get_name()
        try:
            while True:
                request = await self.dequeue()
                response = await self.downloader.fetch(request)
                self.task_done()
                if response is None or response.text is None:
                    continue
                async for result in request.callback(response):
                    if isinstance(result, Request):
                        await self.enqueue(result)
        except asyncio.CancelledError:
            logger.info('worker %s is cancelled' % worker_name)
        except Exception as e:
            logger.info('worker %s is crushed, exception: %s' % (worker_name, str(e)))
        finally:
            self.workers.pop(worker_name, None)
            await self.release()

    # manager worker used to gracefully exit
    async def manage(self):
        while True:
            await asyncio.sleep(1)
            if self.attempt_to_stop():
                break

    # finalizer and release resources
    async def release(self):
        try:
            await self.downloader.close()
        except Exception as e:
            logger.warn('failed to close downloader: %s' % str(e))
        finally:
            pass
