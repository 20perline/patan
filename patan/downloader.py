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

    def __init__(self):
        self.client = None
        self.downloadmw = DownloaderMiddlewareManager()

    async def close(self):
        if self.client is not None:
            await self.client.close()
            self.client = None
            logger.info('downloader is closed now')

    async def fetch(self, request, spider):
        if self.client is None:
            self.client = aiohttp.ClientSession()
        try:
            return await self._fetch(request, spider)
        except aiohttp.client_exceptions.ClientOSError as e:
            logger.error('%s fetch client exception: %s' % (request, e))
        except asyncio.exceptions.TimeoutError:
            logger.error('%s timed out' % request)
        except Exception as e:
            logger.error('%s fetch exception: %s' % (request, e))
        return None

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
        timeout = request.meta.pop('timeout', 300)
        async with self.client.get(request.url, headers=request_headers, timeout=timeout) as http_resp:
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
