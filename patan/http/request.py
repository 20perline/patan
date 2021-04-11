# _*_ coding: utf-8 _*_
from typing import Dict
from typing import Callable
from dataclasses import dataclass
from dataclasses import field


@dataclass
class Request:
    url: str
    method: str = 'GET'
    encoding: str = 'utf-8'
    headers: Dict = field(default_factory=dict)
    cookies: Dict = field(default_factory=dict)
    meta: Dict = field(default_factory=dict)
    callback: Callable = None
    cb_kwargs: Dict = field(default_factory=dict)

    def __hash__(self):
        return hash((self.method, self.url))

    def __str__(self):
        return "%s %s" % (self.method, self.url)
