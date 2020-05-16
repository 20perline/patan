# _*_ coding: utf-8 _*_
from patan.spiders import BaseSpider


class {_capitalize_spider_name}Spider(BaseSpider):

    name = '{_spider_name}'
    start_urls = []

    def parse(self, response):
        # extract item from response
        # yield item
        # or to follow requests
        # yield Request(url=xxx)
        pass
