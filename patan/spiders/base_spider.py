# _*_ coding: utf-8 _*_

import logging
from ..http import Request


logger = logging.getLogger(__name__)

class BaseSpider(object):

    start_urls = []
    encoding = 'utf-8'

    def __init__(self):
        pass

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse_list, encoding=self.encoding)

    def parse_list(self, response):
        return


    def parse_item(self, response):
        return
