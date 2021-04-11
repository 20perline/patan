# _*_ coding: utf-8 _*_
from typing import Dict
from dataclasses import dataclass
from dataclasses import field
from .request import Request


@dataclass
class Response:
    url: str
    status: int = None
    headers: Dict = field(default_factory=dict)
    body: str = ''
    request: Request = None

    @property
    def meta(self):
        return self.request.meta

    def __str__(self):
        return "%s %s" % (self.status, self.url)
