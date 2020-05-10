# _*_ coding: utf-8 _*_

from importlib import import_module


def is_iterable(var):
    return hasattr(var, '__iter__')


def to_iterable(var):
    if var is None:
        return []
    elif is_iterable(var):
        return var
    else:
        return [var]


def load_class_by_name(qualified_name):
    last_dot = qualified_name.rindex('.')
    module, name = qualified_name[:last_dot], qualified_name[last_dot + 1:]
    mod = import_module(module)
    obj = getattr(mod, name)
    return obj


def get_obj_by_class(cls, settings, *args, **kwargs):
    if settings is None:
        raise ValueError('settings not found')
    if hasattr(cls, 'from_settings'):
        return cls.from_settings(settings, *args, **kwargs)
    else:
        return cls(*args, **kwargs)
