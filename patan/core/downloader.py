# _*_ coding: utf-8 _*_

import logging
import aiohttp
from ..http import Response

logger = logging.getLogger(__name__)

class Downloader(object):

    def __init__(self, loop):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
            "Accept-Encoding": "gzip"}
        self.loop = loop
        self.session = None

    async def fetch(self, request, spider):
        if not self.session:
            self.session = aiohttp.ClientSession(loop=self.loop, headers=self.headers)
        response = await self.session.get(request.url, encoding=request.encoding)
        text = await response.text(request.encoding)
        await response.release()
        return Response(text=text)

    def close(self):
        if self.session:
            self.session.close()