# _*_ coding: utf-8 _*_

from . import DownloaderMiddleware
from ..__version__ import __version__


class UserAgentMiddleware(DownloaderMiddleware):

    def __init__(self, ua=None):
        self.user_agent = ua

    @classmethod
    def from_settings(cls, settings):
        ua = settings.get('downloader.http.user_agent')
        if ua is None or len(ua) == 0:
            ua = 'Patan %s' % __version__
        return cls(ua)

    def before_fetch(self, request, spider):
        if self.user_agent:
            request.headers['User-Agent'] = self.user_agent
