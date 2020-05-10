# _*_ coding: utf-8 _*_

import logging
from . import SpiderMiddleware
from ..exceptions import IgnoreRequest

logger = logging.getLogger(__name__)


class HttpErrorMiddleware(SpiderMiddleware):

    def __init__(self):
        pass

    def before_parse(self, response, spider):
        if 200 <= response.status < 400:
            return
        logger.info('%s ignored: HTTP ERROR' % response)
        raise IgnoreRequest()
