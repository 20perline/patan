# _*_ coding: utf-8 _*_
# define spider middlewares and downloader middlewares
# clear out the content of this file if you don't any middleware

from patan.spidermws import SpiderMiddleware
from patan.downloadermws import DownloaderMiddleware


class {_capitalize_project_name}SpiderMiddleware(SpiderMiddleware):

    @classmethod
    def from_settings(cls, settings):
        # patan will create middleware for you using this class method while injecting the project settings
        return cls()

    def before_parse(self, response, spider):
        # response come from downloader middleware output
        # this is the entry point you want to make some change before passing the response to spider
        # return None or raise Exception
        return

    def after_parse(self, response, result, spider):
        # result come from spider parse output or other spider middlewares
        # this is the entry point you want to make some change before passing the result to pipeline
        # return an iterable of Request or items.
        return result

    def when_exception(self, response, exception, spider):
        # this will be called when there's an exception calling the *parse method or spider itself
        # you can still return Requests or items, same as after_parse
        return


class {_capitalize_project_name}DownloaderMiddleware(DownloaderMiddleware):

    @classmethod
    def from_settings(cls, settings):
        # patan will create middleware for you using this class method while injecting the project settings
        return cls()

    def before_fetch(self, request, spider):
        # request pulled from scheduler
        # this is the entry point you want to make some change before passing the response to downloader
        # downloader will continue handle when returning None
        # downloader will stop handle chain when returning Request or Response
        # request will cancelled when there's an exception raised
        return

    def after_fetch(self, request, response, spider):
        # response come after downloader finish fetching the response
        # this is the entry point you want to make some change before passing the response to spider
        # return Request or Response or raise an exception
        return response

    def when_exception(self, request, exception, spider):
        # handle exception when there's exception for before_fetch
        # return either Request or Response will stop the handler chain
        return
