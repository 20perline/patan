# _*_ coding: utf-8 _*_


class Response(object):

    def __init__(self, request=None, headers=None, text=None):
        self.request = request
        self.headers = headers
        self.text = text
