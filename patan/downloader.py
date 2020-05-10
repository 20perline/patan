# _*_ coding: utf-8 _*_

import logging
import aiohttp
import asyncio
import traceback
from .http.request import Request
from .http.response import Response
from .middleware import DownloaderMiddlewareManager

logger = logging.getLogger(__name__)


class Downloader(object):

    def __init__(self, settings):
        self.client = None
        self.settings = settings
        self.max_concurrency = self.settings.get('downloader.concurrent_requests')
        self.active = set()
        self.downloadmw = DownloaderMiddlewareManager.from_settings(self.settings)

    @classmethod
    def from_settings(cls, settings):
        return cls(settings)

    def available(self):
        return len(self.active) < self.max_concurrency

    async def close(self):
        if self.client is not None:
            await self.client.close()
            self.client = None
            logger.info('downloader is closed now')

    async def fetch(self, request, spider):
        if self.client is None:
            self.client = aiohttp.ClientSession()
        result = None
        try:
            self.active.add(request)
            result = await self._fetch(request, spider)
        except aiohttp.client_exceptions.ClientOSError as e:
            logger.error('%s fetch client exception: %s' % (request, e))
        except asyncio.exceptions.TimeoutError:
            logger.error('%s timed out' % request)
        except Exception as e:
            logger.error('%s fetch exception: %s' % (request, e))
        finally:
            self.active.remove(request)
        return result

    async def _fetch(self, request, spider):
        logger.info(request)
        try:
            mw_res = self.downloadmw.handle_request(request, spider)
            if isinstance(mw_res, (Request, Response)):
                return mw_res
        except Exception as e:
            logger.warn("%s downloader middleware chain aborted, exception: %s \n%s" % (request, e, traceback.format_exc()))
            mw_res = self.downloadmw.handle_exception(request, e, spider)
            if isinstance(mw_res, (Request, Response)):
                return mw_res

        response = None
        request_headers = request.headers
        timeout = request.meta.pop('timeout')
        proxy = self.settings.get('downloader.http.proxy')
        async with self.client.get(request.url, headers=request_headers, timeout=timeout, cookies=request.cookies, proxy=proxy) as http_resp:
            content = await http_resp.text(request.encoding)
            response = Response(
                url=request.url,
                status=http_resp.status,
                headers=http_resp.headers,
                body=content,
                request=request
            )
        logger.info(response)
        try:
            response = self.downloadmw.handle_response(request, response, spider)
        except Exception as e:
            logger.warn("%s downloader middleware chain aborted, exception: %s \n%s" % (request, e, traceback.format_exc()))
        return response
