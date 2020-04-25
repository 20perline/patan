# _*_ coding: utf-8 _*_
from .request import Request
import logging

logger = logging.getLogger(__name__)


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
        url = request.url
        if url not in self.seen:
            self.seen.add(url)
            return False
        logger.debug('>>> {} skipped'.format(url))
        return True
