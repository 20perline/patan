# _*_ coding: utf-8 _*_

import logging
import aiohttp
import mimetypes
import os
from urllib.parse import urlsplit
from .request import Request


logger = logging.getLogger(__name__)


class BaseSpider(object):

    start_urls = []
    encoding = 'utf-8'

    def __init__(self):
        self.downloader = None

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse, encoding=self.encoding)

    async def close(self):
        if self.downloader is not None:
            await self.downloader.close()
        logger.info('spider is closed now')

    def ensure_downloader(self):
        if self.downloader is None:
            self.downloader = aiohttp.ClientSession()

    def get_base_url(self, url):
        return "{0.scheme}://{0.netloc}".format(urlsplit(url))

    async def download_image(self, url, save_dir, save_as):
        self.ensure_downloader()
        try:
            async with self.downloader.get(url) as resp:
                content_type = resp.content_type
                ext = mimetypes.guess_extension(content_type) or '.jpg'
                abs_file_path = os.path.join(save_dir, '{}.{}'.format(save_as, ext))
                if resp.status == 200:
                    with open(abs_file_path, mode='wb') as imgfile:
                        imgfile.write(await resp.read())
            logger.info('image {} saved successfully.'.format(url))
        except aiohttp.client_exceptions.ClientOSError as e:
            logger.error('failed to save image %s : %s' % (url, e))
            return
        except Exception as e:
            logger.error('failed to save image %s : %s' % (url, str(e)))
            return

    async def parse(self, response):
        return
