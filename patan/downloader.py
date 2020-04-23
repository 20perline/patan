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
        
    async def fetch(self, request):
        if self.client is None:
            self.client = aiohttp.ClientSession(headers=self.headers)
        try:
            async with self.client.get(request.url) as resp:
                content = await resp.text(request.encoding)
                return Response(request=request, text=content)
        except Exception as e:
            logger.error('<'*6 + ' ' + request.url + ' failed' + e.message)
            return None
