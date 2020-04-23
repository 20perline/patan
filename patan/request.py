# _*_ coding: utf-8 _*_


class Request(object):

    def __init__(self, url=None, callback=None, encoding='utf-8'):
        self.url = url
        self.callback = callback
        self.encoding = encoding
