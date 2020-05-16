# _*_ coding: utf-8 _*_
import logging
import inspect
import traceback
from . import utils
from .http.request import Request
from .http.response import Response


logger = logging.getLogger(__name__)


class MiddlewareManager(object):

    def __init__(self, *middlewares):
        self.middlewares = middlewares
        if self.middlewares is not None and len(self.middlewares) > 0:
            for mw in self.middlewares:
                logger.info('enable middleware %s' % type(mw).__name__)


class DownloaderMiddlewareManager(MiddlewareManager):

    def __init__(self, *middlewares):
        super().__init__(*middlewares)

    @classmethod
    def from_settings(cls, settings):
        middlewares = []
        for mw in settings.get_sorted_list('downloader.middlewares'):
            mw_cls = utils.load_class_by_name(mw)
            mw_obj = utils.get_obj_by_class(mw_cls, settings)
            middlewares.append(mw_obj)
        return cls(*middlewares)

    '''each middleware should return None if thing goes right, also will return Request or Response object if necessary'''
    def handle_request(self, request, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return

        for mw in self.middlewares:
            mw_result = mw.before_fetch(request, spider)
            if mw_result is None:
                continue
            if isinstance(mw_result, (Request, Response)):
                return mw_result

    '''if some middleware return a Request object, will return that object and skip the rest of middlewares'''
    def handle_response(self, request, response, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return response

        for mw in self.middlewares:
            response = mw.after_fetch(request, response, spider)
            if isinstance(response, Response):
                continue
            if isinstance(response, Request):
                return response
        return response

    '''return None or Request or Response'''
    def handle_exception(self, request, exception, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return

        for mw in self.middlewares:
            response = mw.when_exception(request, exception, spider)
            if isinstance(response, (Request, Response)):
                return response
        return response


class SpiderMiddlewareManager(MiddlewareManager):

    def __init__(self, *middlewares):
        super().__init__(*middlewares)

    @classmethod
    def from_settings(cls, settings):
        middlewares = []
        for mw in settings.get_sorted_list('spider.middlewares'):
            mw_cls = utils.load_class_by_name(mw)
            mw_obj = utils.get_obj_by_class(mw_cls, settings)
            middlewares.append(mw_obj)
        return cls(*middlewares)

    '''each middleware will return None or raise an Exception'''
    def handle_input(self, response, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return

        for mw in self.middlewares:
            mw.before_parse(response, spider)

    '''return type could be Iterable of Request or Items'''
    def handle_output(self, response, result, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return result

        for mw in self.middlewares:
            result = mw.after_parse(response, result, spider)

        return result

    '''return None or Iterable'''
    def handle_exception(self, response, exception, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return

        for mw in self.middlewares:
            result = mw.when_exception(response, exception, spider)
            if result is not None:
                return result

        return


class PipelineManager(MiddlewareManager):

    def __init__(self, *middlewares):
        super().__init__(*middlewares)

    @classmethod
    def from_settings(cls, settings):
        middlewares = []
        for mw in settings.get_sorted_list('pipelines'):
            mw_cls = utils.load_class_by_name(mw)
            mw_obj = utils.get_obj_by_class(mw_cls, settings)
            middlewares.append(mw_obj)
        return cls(*middlewares)

    '''process item'''
    async def process_item(self, item, spider):
        if self.middlewares is None or len(self.middlewares) == 0:
            return

        for mw in self.middlewares:
            attr = getattr(mw, 'process_item', None)
            if attr is None:
                logger.warn('pipeline %s has no attr named process_item' % type(mw).__name__)
                continue
            try:
                result = mw.process_item(item, spider)
                if inspect.iscoroutine(result):
                    await result
            except Exception:
                logger.error("process item exception: %s \n%s" % (item, traceback.format_exc()))
