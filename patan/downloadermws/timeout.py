# _*_ coding: utf-8 _*_

from . import DownloaderMiddleware


class DownloadTimeoutMiddleware(DownloaderMiddleware):

    def __init__(self, timeout):
        self.timeout = timeout

    @classmethod
    def from_settings(cls, settings):
        timeout = settings.get('downloader.timeout')
        return cls(timeout)

    def before_fetch(self, request, spider):
        if self.timeout:
            request.meta['timeout'] = self.timeout
