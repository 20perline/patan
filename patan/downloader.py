# _*_ coding: utf-8 _*_

import logging
import aiohttp
import asyncio
import traceback
from aiohttp_sse_client import client as aio_sse_client
from .http.request import Request
from .http.response import Response
from .middleware import DownloaderMiddlewareManager

logger = logging.getLogger(__name__)


class Downloader(object):

    def __init__(self, settings):
        self.client = None
        self.sse_client = None
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
        if self.sse_client is not None:
            await self.sse_client.close()
            self.sse_client = None
        logger.info('downloader is closed now')

    async def fetch(self, request, spider):
        result = None
        try:
            self.active.add(request)
            is_sse_req = request.meta.get('is_sse', False)
            if is_sse_req:
                result = await self._fetch_sse(request, spider)
            else:
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

    '''using default aiohttp client'''
    async def _fetch(self, request, spider):
        if self.client is None:
            self.client = aiohttp.ClientSession()
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

    '''using sse client'''
    async def _fetch_sse(self, request, spider):
        if self.sse_client is None:
            self.sse_client = aiohttp.ClientSession()
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
        async with aio_sse_client.EventSource(request.url, session=self.sse_client, option=dict(headers=request_headers)) as event_source:
            async for event in event_source:
                response = Response(
                    url=request.url,
                    status=200,
                    body=event.data,
                    request=request
                )
                break
        logger.info(response)
        try:
            response = self.downloadmw.handle_response(request, response, spider)
        except Exception as e:
            logger.warn("%s downloader middleware chain aborted, exception: %s \n%s" % (request, e, traceback.format_exc()))
        return response
