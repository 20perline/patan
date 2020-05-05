# _*_ coding: utf-8 _*_


def is_iterable(self, var):
    return hasattr(var, '__iter__')


def to_iterable(self, var):
    a = []
    for i in var:
        a.append(i)
    return a
