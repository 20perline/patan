# _*_ coding: utf-8 _*_

import logging
import asyncio
import traceback
from dataclasses import is_dataclass
from .http.request import Request
from .http.response import Response
from .scheduler import Scheduler
from .downloader import Downloader
from .middleware import SpiderMiddlewareManager
from .middleware import PipelineManager

logger = logging.getLogger(__name__)


class Engine(object):

    def __init__(self, settings):
        self.settings = settings
        self.workers_num = self.settings.get('engine.workers_num')
        self.workers_waiting = set()
        self.workers = []
        self.spiders = dict()
        self.scheduler = Scheduler.from_settings(self.settings)
        self.downloader = Downloader.from_settings(self.settings)
        self.spidermw = SpiderMiddlewareManager.from_settings(self.settings)
        self.pipeline = PipelineManager.from_settings(self.settings)

    def add_spider(self, spider=None):
        if spider is None:
            raise ValueError('unknown spider')
        self.spiders.update({spider.name: spider})

    def _attach_spider(self, request, spider):
        if 'sp' not in request.meta:
            request.meta['sp'] = spider.name

    def _detect_spider(self, request):
        return self.spiders.get(request.meta['sp'])

    async def bootstrap(self):
        if len(self.spiders) == 0:
            logger.error('no spiders available, exiting now.')
            exit()
        for spider in self.spiders.values():
            for req in spider.start_requests():
                self._attach_spider(req, spider)
                self.scheduler.enqueue_nowait(req)

        # create all workers and start concurrently
        for _ in range(self.workers_num):
            name = 'Worker-{:0>2d}'.format(_)
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
            logger.info('%s is cancelled' % worker_name)
        except Exception as e:
            logger.info('%s is crushed, exception: %s' % (worker_name, str(e)))
            logger.error(traceback.format_exc())

    async def _work(self, worker_name):
        while True:
            logger.debug('%s is waiting for new request...' % (worker_name))
            self.workers_waiting.add(worker_name)
            request = await self.scheduler.next_request()
            self.workers_waiting.remove(worker_name)

            spider = self._detect_spider(request)
            try:
                while not self.downloader.available():
                    await asyncio.sleep(0.05)
                response = await self.downloader.fetch(request, spider)
            finally:
                self.scheduler.ack_last_request()

            # check downloader return type
            if not isinstance(response, (Request, Response)):
                logger.debug('request %s got invalid response' % request)
                continue
            # some middleware might return requests
            if isinstance(response, Request):
                self._attach_spider(response, spider)
                self._schedule_request(response)
                continue

            # walk through all spider middlewares
            try:
                self.spidermw.handle_input(response, spider)
                callback = request.callback
                cb_res = callback(response, **request.cb_kwargs)
                response = self.spidermw.handle_output(response, cb_res, spider)
            except Exception as e:
                logger.warn("%s spider middleware chain aborted, exception: %s \n%s" % (response, e, traceback.format_exc()))
                response = self.spidermw.handle_exception(response, e, spider)
            if response is None:
                continue
            for resp in response:
                if isinstance(resp, Request):
                    self._attach_spider(resp, spider)
                    self._schedule_request(resp)
                elif is_dataclass(resp):
                    await self.pipeline.process_item(resp, spider)

    # create another temp task to schedule the new request , otherwise it will block the workers (producer mostly faster than consumer)
    def _schedule_request(self, request):
        asyncio.create_task(self.scheduler.enqueue(request))

    # manager worker used to gracefully exit
    async def manage(self):
        while True:
            await asyncio.sleep(1)
            if len(self.workers) == 0:
                continue
            # when scheduler's queue is empty and all workers are idle
            # manager worker will terminate the engine
            if self.scheduler.has_pending_requests() and len(self.workers_waiting) == self.workers_num:
                for worker in self.workers:
                    worker.cancel()
                break

    # shutdown the engine and finalize resources
    async def shutdown(self):
        try:
            await self.downloader.close()
            for sp, spider in self.spiders.items():
                spider.close()
        except Exception as e:
            logger.warn('failed to close components: %s' % e)
        finally:
            logger.info('engine is shutdown now')

    def start(self):
        try:
            asyncio.run(self.bootstrap())
        except KeyboardInterrupt:
            logger.info('engine was shutdown by force')
