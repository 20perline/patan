# _*_ coding: utf-8 _*_

import logging
from . import SpiderMiddleware
from ..http.request import Request

logger = logging.getLogger(__name__)


class DepthMiddleware(SpiderMiddleware):

    def __init__(self, maxdepth):
        self.maxdepth = maxdepth

    @classmethod
    def from_settings(cls, settings):
        depth_limit = settings.get('spider.depth_limit')
        return cls(depth_limit)

    def after_parse(self, response, result, spider):
        if 'depth' not in response.meta:
            response.meta['depth'] = 0
        resp_depth = response.meta['depth']
        return (r for r in result or () if self._check_depth(r, resp_depth))

    def _check_depth(self, request, resp_depth):
        if isinstance(request, Request):
            depth = resp_depth + 1
            request.meta['depth'] = depth
            if self.maxdepth > 0 and depth > self.maxdepth:
                logger.warn('%s depth > %d, skipped' % (request, self.maxdepth))
                return False
        return True
