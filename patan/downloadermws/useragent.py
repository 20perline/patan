# _*_ coding: utf-8 _*_

from . import DownloaderMiddleware


class UserAgentMiddleware(DownloaderMiddleware):

    def __init__(self, ua='Patan'):
        self.user_agent = ua

    def before_fetch(self, request, spider):
        if self.user_agent:
            request.headers['User-Agent'] = self.user_agent
