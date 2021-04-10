# _*_ coding: utf-8 _*_
# define item class using dataclass

from dataclasses import dataclass


@dataclass(init=False)
class StockItem:
    name: str
    code: str
    ddx: int = None
