# _*_ coding: utf-8 _*_
import os
import json
from glom import glom


class Settings(object):

    def __init__(self, project_settings_file=None):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        default_file = os.path.join(dir_path, 'default.json')
        with open(default_file) as file:
            default_settings = json.loads(file.read())
        project_settings = {}
        if project_settings_file is not None:
            with open(project_settings_file) as file:
                project_settings = json.loads(file.read())

        self.data = self._merge(default_settings, project_settings)

    def _merge(self, src, target):
        for key, value in target.items():
            if key not in src:
                src[key] = value
                continue
            if isinstance(value, dict) and isinstance(src[key], dict):
                self._merge(src[key], value)
            elif src[key] == value:
                pass
            elif isinstance(value, list) and isinstance(src[key], list):
                src[key] = src[key] + value
            else:
                src[key] = value
        return src

    def get(self, key, default=None):
        return glom(self.data, key, default=default)

    def get_sorted_list(self, key, default=None):
        if default is None:
            default = []
        val = self.get(key, default)
        if isinstance(val, dict):
            val = [k for k, v in sorted(val.items(), key=lambda item: item[1])]
        if isinstance(val, list):
            val = sorted(val)
        return val
