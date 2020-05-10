# _*_ coding: utf-8 _*_


class SpiderMiddleware(object):

    def before_parse(self, response, spider):
        return

    def after_parse(self, response, result, spider):
        return result

    def when_exception(self, response, exception, spider):
        return
