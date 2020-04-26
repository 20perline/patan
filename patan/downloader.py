# _*_ coding: utf-8 _*_

import logging
import aiohttp
from .response import Response

logger = logging.getLogger(__name__)


class Downloader(object):

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            "Accept-Encoding": "gzip"}
        self.client = None

    async def close(self):
        if self.client is not None:
            await self.client.close()
            self.client = None
            logger.info('downloader is closed now')

    async def fetch(self, request):
        if self.client is None:
            self.client = aiohttp.ClientSession(headers=self.headers)
        url = request.url
        logger.info('>>> ' + url)
        try:
            async with self.client.get(url) as resp:
                content = await resp.text(request.encoding)
                logger.info('<<< ' + url)
                return Response(url=resp.url, status=resp.status, headers=resp.headers, text=content)
        except aiohttp.client_exceptions.ClientOSError as e:
            logger.error('<<< %s failed: %s' % (url, e))
            return None
        except Exception as e:
            logger.error('<<< %s failed: %s' % e.message)
            return None
