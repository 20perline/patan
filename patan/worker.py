# _*_ coding: utf-8 _*_

from dataclasses import dataclass
from asyncio import Future


'''real worker in scheduler'''
@dataclass
class Worker(object):
    task: Future
    name: str
    status: int
