# _*_ coding: utf-8 _*_

import sys
import logging
import hashlib
import os
sys.path.append('../patan')
from patan.engine import Engine
from patan.spiders import BaseSpider
from patan.request import Request
from patan import utils
from bs4 import BeautifulSoup
from pathlib import Path

logger = logging.getLogger(__name__)


class BeautySpider(BaseSpider):

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
    async def parse(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
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
        md5 = hashlib.md5()
        root_dir = os.path.join(str(Path.home()), 'Downloads', 'SSNI674')
        for image in images:
            url = image.get('src')
            md5.update(url.encode(encoding='utf-8'))
            await self.download_image(url, root_dir, md5.hexdigest())


engine = Engine(spider=BeautySpider(), worker_num=20)
engine.start()
