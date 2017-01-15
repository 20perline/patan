# _*_ coding: utf-8 _*_

import logging
import sys
from patan.core import Engine
from patan.spiders import BaseSpider
from patan.http import Request
from bs4 import BeautifulSoup

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

class MeinvSpider(BaseSpider):

    start_urls = [
        'http://www.meinv.tw/xinggan/',
        'http://www.meinv.tw/qingchun/'
    ]

    def parse_list(self, response):
        try:
            soup = BeautifulSoup(response.text, 'html5lib')
            entries = soup.select('div.m-list-main div.u-img a')
            if not entries:
                return
            for entry in entries:
                href = entry.get('href')
                yield Request(url=href, callback=self.parse_item)

            next_page_tag = soup.select('div.m-page a.next')
            if next_page_tag:
                href = next_page_tag[0].get('href')
                yield Request(url=href, callback=self.parse_list)
        except Exception as err:
            logging.error(err)
            return


    def parse_item(self, response):
        try:
            soup = BeautifulSoup(response.text, 'html5lib')
            next_page_span = soup.find('span', text='下一页')
            if next_page_span:
                href = next_page_span.parent.get('href')
                yield Request(url=href, callback=self.parse_item)
            image = soup.select('div.m-list-content > p img')
            if image is None or len(image) == 0:
                return
            url = image[0].get('src')
            # filename = response.url_obj.path.lstrip('/').rstrip('.html').replace('/', '_') + '.jpg'
            logging.info('downloading image: {}'.format(url))
        except Exception as err:
            logging.error(err)
            return


engine = Engine(spider=MeinvSpider())
engine.start()
