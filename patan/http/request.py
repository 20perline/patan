# _*_ coding: utf-8 _*_


class Request(object):

    def __init__(self,
                 url=None,
                 method='GET',
                 headers=None,
                 callback=None,
                 meta=None,
                 encoding='utf-8',
                 cookies=None,
                 body=None):

        if callback is not None and not callable(callback):
            raise TypeError('callback must be a callable')
        self.callback = callback
        self.url = url
        self.encoding = encoding
        self.method = str(method).upper()
        self.headers = headers or {}
        self.cookies = cookies or {}
        # sp: spider name
        # timeout: downloader timeout
        self.meta = meta or {}

    def __str__(self):
        return "<%s %s>" % (self.method, self.url)
