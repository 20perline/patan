# _*_ coding: utf-8 _*_

from .http.request import Request
import logging

logger = logging.getLogger(__name__)


class BaseDupFilter(object):

    def __init__(self):
        pass

    def seen(self, request):
        return False


class SimpleDupFilter(BaseDupFilter):

    def __init__(self):
        super().__init__()
        self.item_set = set()

    def seen(self, request: Request):
        url = request.url
        if url not in self.item_set:
            self.item_set.add(url)
            return False
        logger.debug('Skip {}'.format(url))
        return True
