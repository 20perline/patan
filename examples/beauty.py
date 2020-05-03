# _*_ coding: utf-8 _*_

import sys
import logging
sys.path.append('../patan')
from patan.patan import Patan
from patan.spiders import BaseSpider
from patan.http.request import Request
from patan import utils
from bs4 import BeautifulSoup
from pathlib import Path

logger = logging.getLogger(__name__)


class BeautySpider(BaseSpider):

    name = 'beauty'
    start_urls = [
        'http://www.656g.com/meinv/xinggan/10373.html'
    ]

    # async def parse(self, response):
    #     soup = BeautifulSoup(response.text, 'html.parser')
    #     entries = soup.select('div.page >a')
    #     if not entries:
    #         return
    #     for entry in entries:
    #         if entry.get('href') is None:
    #             continue
    #         href = self.get_base_url(str(response.url)) + entry.get('href')
    #         if not href.startswith('#'):
    #             yield Request(url=href, callback=self.parse)
    #     albums = soup.select('div.m-list >ul >li >a')
    #     if not albums:
    #         return
    #     for album in albums:
    #         if album.get('href') is None:
    #             continue
    #         href = self.get_base_url(str(response.url)) + album.get('href')
    #         if not href.startswith('#'):
    #             yield Request(url=href, callback=self.parse_item)

    # async def parse_item(self, response):
    def parse(self, response):
        soup = BeautifulSoup(response.body, 'html.parser')
        entries = soup.select('div.page >a')
        if not entries:
            return
        for entry in entries:
            if entry.get('href') is None:
                continue
            href = utils.get_base_url(str(response.url)) + entry.get('href')
            if not href.startswith('#'):
                yield Request(url=href, callback=self.parse)
        images = soup.select('div.pic-main >a >img')
        if images is None or len(images) == 0:
            return
        for image in images:
            url = image.get('src')
            logger.info('image %s' % url)


if __name__ == '__main__':
    patan = Patan()
    patan.crawl(BeautySpider())
    patan.start()
