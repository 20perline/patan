# _*_ coding: utf-8 _*_
from ..http import Request

class BaseDupFilter(object):

    def __init__(self):
        pass


    def request_seen(self, request):
        return False



class SimpleDupFilter(BaseDupFilter):

    def __init__(self):
        super().__init__()
        self.seen = set()

    def request_seen(self, request: Request):
        if not request.url in self.seen:
            self.seen.add(request.url)
            return False
        return True
