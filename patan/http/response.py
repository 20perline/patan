# _*_ coding: utf-8 _*_

class Response(object):

    def __init__(self, headers=None, text=None):
        self.headers = headers
        self.text = text
