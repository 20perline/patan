# _*_ coding: utf-8 _*_
import logging
from .http.request import Request
from .http.response import Response
from .downloadermws.timeout import DownloadTimeoutMiddleware
from .downloadermws.useragent import UserAgentMiddleware
from .spidermws.depth import DepthMiddleware

logger = logging.getLogger(__name__)


class MiddlewareManager(object):

    def __init__(self, middlewares=None):
        self.middlewares = middlewares
        if self.middlewares is not None and len(self.middlewares) > 0:
            for mw in self.middlewares:
                logger.info('enable middleware %s' % type(mw).__name__)


class DownloaderMiddlewareManager(MiddlewareManager):

    def __init__(self, middlewares=None):
        if middlewares is None:
            middlewares = []
        middlewares.append(UserAgentMiddleware())
        middlewares.append(DownloadTimeoutMiddleware())
        super().__init__(middlewares)

    def handle_request(self, request, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return

        try:
            for mw in self.middlewares:
                mw_result = mw.before_fetch(request, spider)
                if mw_result is None:
                    continue
                if isinstance(mw_result, (Request, Response)):
                    return mw_result
        except Exception as e:
            logger.warn('downloader middleware failed to handle %s, cancelling other before middlewares: %s' % (request, e))

        return

    def handle_response(self, request, response, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return response

        try:
            for mw in self.middlewares:
                response = mw.after_fetch(request, response, spider)
                if isinstance(response, Response):
                    continue
                if isinstance(response, Request):
                    return response
        except Exception as e:
            logger.warn('downloader middleware failed to handle %s, cancelling other after middlewares: %s' % (request, e))
            raise e
        return response


class SpiderMiddlewareManager(MiddlewareManager):

    def __init__(self, middlewares=None):
        if middlewares is None:
            middlewares = []
        middlewares.append(DepthMiddleware())
        super().__init__(middlewares)

    def handle_input(self, response, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return

        try:
            for mw in self.middlewares:
                ret = mw.before_parse(response, spider)
                if ret is None:
                    continue
                else:
                    break
        except Exception as e:
            logger.warn('spider middleware failed to handle response %s, cancelling other input middlewares: %s' % (response, e))

        return

    def handle_output(self, response, result, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return self._to_iterable(result)

        try:
            for mw in self.middlewares:
                result = mw.after_parse(response, self._to_iterable(result), spider)
        except Exception as e:
            logger.warn('spider middleware failed to handle result %s, cancelling other output middlewares: %s' % (result, e))
            return {}

        return self._to_iterable(result)

    def _is_iterable(self, var):
        return hasattr(var, '__iter__')

    def _to_iterable(self, var):
        a = []
        for i in var:
            a.append(i)
        return a
