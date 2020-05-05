# _*_ coding: utf-8 _*_


class DownloaderMiddleware(object):

    def before_fetch(self, request, spider):
        return

    def after_fetch(self, request, response, spider):
        return response

    def when_exception(self, request, exception, spider):
        return
