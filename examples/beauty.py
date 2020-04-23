# _*_ coding: utf-8 _*_

import logging
import sys
from patan.engine import Engine
from patan.spiders import BaseSpider
from patan.request import Request
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import os
import hashlib

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


class BeautySpider(BaseSpider):

    host = 'http://www.656g.com'

    start_urls = [
        'http://www.656g.com/meinv/xinggan/18317.html'
    ]

    async def parse(self, response):
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            entries = soup.select('div.page >a')
            if not entries:
                return
            for entry in entries:
                if entry.get('href') is None:
                    continue
                href = self.host + entry.get('href')
                if not href.startswith('#'):
                    yield Request(url=href, callback=self.parse)
            images = soup.select('div.pic-main >a >img')
            if images is None or len(images) == 0:
                return
            md5 = hashlib.md5()
            for image in images:
                url = image.get('src')
                md5.update(url.encode(encoding='utf-8'))
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            f = await aiofiles.open(os.path.join('c:', '/Users/******/Downloads/SSNI674', md5.hexdigest() + '.jpg'), mode='wb')
                            await f.write(await resp.read())
                            await f.close()
                logger.info('<'*6 + ' ' + url)

        except Exception as err:
            logger.error(err)
            return


engine = Engine(spider=BeautySpider())
engine.start()
