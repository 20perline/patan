# _*_ coding: utf-8 _*_


class Response(object):

    def __init__(self, url=None, status=None, headers=None, text=None):
        self.status = status
        self.url = url
        self.headers = headers
        self.text = text
