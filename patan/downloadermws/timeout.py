# _*_ coding: utf-8 _*_

from . import DownloaderMiddleware


class DownloadTimeoutMiddleware(DownloaderMiddleware):

    def __init__(self, timeout=60):
        self.timeout = timeout

    def before_fetch(self, request, spider):
        if self.timeout:
            request.meta['timeout'] = self.timeout
