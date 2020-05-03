# _*_ coding: utf-8 _*_
import logging
from .http.request import Request
from .http.response import Response
from .downloadermws.timeout import DownloadTimeoutMiddleware
from .downloadermws.useragent import UserAgentMiddleware
from .spidermws.depth import DepthMiddleware
from .spidermws.httperror import HttpErrorMiddleware

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

    '''each middleware should return None if thing goes right, also will return Request or Response object if necessary'''
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

    '''if some middleware return a Request object, will return that object and skip the rest of middlewares'''
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
        middlewares.append(HttpErrorMiddleware())
        middlewares.append(DepthMiddleware())
        super().__init__(middlewares)

    '''response will be None if exception occurred'''
    def handle_input(self, response, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return

        try:
            for mw in self.middlewares:
                mw.before_parse(response, spider)
        except Exception as e:
            logger.warn('spider middleware failed to handle response %s, cancelling other input middlewares: %s' % (response, e))
            response = None

        return

    '''return type could be Iterable of Request or Items'''
    def handle_output(self, response, result, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return result

        try:
            for mw in self.middlewares:
                result = mw.after_parse(response, result, spider)
        except Exception as e:
            logger.warn('spider middleware failed to handle result %s, cancelling other output middlewares: %s' % (result, e))
            return None

        return result
