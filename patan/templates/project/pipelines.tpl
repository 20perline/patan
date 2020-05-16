# _*_ coding: utf-8 _*_
# A class with a method process_item(item, spider) will be treated as a pipeline


class {_capitalize_project_name}Pipeline:

    @classmethod
    def from_settings(cls, settings):
        # patan will create pipeline for you using this class method while injecting the project settings
        # you're free to remove this if there's no need
        return cls()

    def process_item(self, item, spider):
        pass
