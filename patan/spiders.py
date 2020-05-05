# _*_ coding: utf-8 _*_

import logging
from .http.request import Request


# logger = logging.getLogger(__name__)


class BaseSpider(object):

    name = None
    start_urls = []
    encoding = 'utf-8'

    def __init__(self, name=None):
        if name is not None:
            self.name = name
        elif not getattr(self, 'name', None):
            raise ValueError("spider %s must have a name" % type(self).__name__)

    @property
    def logger(self):
        return logging.getLogger(self.name)

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, encoding=self.encoding)

    def parse(self, response):
        return

    def close(self):
        pass
