# _*_ coding: utf-8 _*_


class Response(object):

    def __init__(self, url=None, status=None, headers=None, body=None, request=None):
        self.status = status
        self.url = url
        self.headers = headers or {}
        self.body = body
        self.request = request

    @property
    def meta(self):
        return self.request.meta

    def __str__(self):
        return "<%d %s>" % (self.status, self.url)
