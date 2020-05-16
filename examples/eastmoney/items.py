# _*_ coding: utf-8 _*_
# define item class using dataclass

from dataclasses import dataclass


@dataclass
class StockItem:
    name: str
    code: str
