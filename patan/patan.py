# _*_ coding: utf-8 _*_

from .engine import Engine


class Patan(object):

    def __init__(self, *args, **kwargs):
        self.engine = Engine()

    def crawl(self, spider):
        self.engine.add_spider(spider)

    def start(self):
        self.engine.start()
