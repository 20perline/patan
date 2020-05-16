# _*_ coding: utf-8 _*_

import sys
import logging
from .spiders import BaseSpider
from .utils import load_class_by_name, get_obj_by_class
from .settings import Settings
from .engine import Engine
from logging import NullHandler


class Patan(object):

    def __init__(self, settings=None):
        self.settings = Settings(settings)

        logging.getLogger(__name__).addHandler(NullHandler())
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.getLevelName(self.settings.get('log.level', 'info').upper()),
            format=self.settings.get('log.format')
        )

        self.engine = Engine(self.settings)

    def crawl(self, spider):
        if isinstance(spider, str):
            spider = get_obj_by_class(load_class_by_name(spider), self.settings)
        if not isinstance(spider, BaseSpider):
            raise TypeError('unknown spider instance')
        self.engine.add_spider(spider)

    def start(self):
        self.engine.start()
