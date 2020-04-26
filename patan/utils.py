# _*_ coding: utf-8 _*_
from urllib.parse import urlsplit


def get_base_url(url):
    return "{0.scheme}://{0.netloc}".format(urlsplit(url))
