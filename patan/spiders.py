# _*_ coding: utf-8 _*_

import logging
from .request import Request


logger = logging.getLogger(__name__)


class BaseSpider(object):

    start_urls = []
    encoding = 'utf-8'

    def __init__(self):
        pass

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, encoding=self.encoding)

    async def parse(self, response):
        return
