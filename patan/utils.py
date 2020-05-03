# _*_ coding: utf-8 _*_
from urllib.parse import urlsplit


def get_base_url(url):
    return "{0.scheme}://{0.netloc}".format(urlsplit(url))


def is_iterable(self, var):
    return hasattr(var, '__iter__')


def to_iterable(self, var):
    a = []
    for i in var:
        a.append(i)
    return a
