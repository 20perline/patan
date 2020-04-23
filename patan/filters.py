# _*_ coding: utf-8 _*_
from .request import Request


class BaseDupFilter(object):

    def __init__(self):
        pass

    def is_duplicated(self, request):
        return False


class SimpleDupFilter(BaseDupFilter):

    def __init__(self):
        super().__init__()
        self.seen = set()

    def is_duplicated(self, request: Request):
        if request.url not in self.seen:
            self.seen.add(request.url)
            return False
        return True
