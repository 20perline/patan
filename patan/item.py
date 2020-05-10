# _*_ coding: utf-8 _*_


class Item(object):

    def __init__(self, *args, **kwargs):
        self._values = {}
        if args or kwargs:
            for k, v in dict(*args, **kwargs).items():
                self[k] = v
