# _*_ coding: utf-8 _*_

import logging
import aiohttp
from .http.response import Response
from .middleware import DownloaderMiddlewareManager

logger = logging.getLogger(__name__)


class Downloader(object):

    def __init__(self):
        self.client = None
        self.middleware = DownloaderMiddlewareManager()

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
            logger.error('<<< %s failed: %s' % (request, e))
            return None
        except Exception as e:
            logger.error('<<< %s failed: %s' % e.message)
            return None

    async def _fetch(self, request, spider):
        logger.info(request)
        self.middleware.handle_request(request, spider)
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
        response = self.middleware.handle_response(request, response, spider)
        return response
