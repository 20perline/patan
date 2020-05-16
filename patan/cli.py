# _*_ coding: utf-8 _*_

import os
import click
import sys
import inspect
from codecs import open
from os.path import join, isdir, dirname, abspath, basename, splitext, normpath, realpath
from importlib import import_module
from .patan import Patan
from .spiders import BaseSpider


@click.group()
def main():
    pass


@main.command('newproject', short_help='create a new project')
@click.argument('project_name')
def newproject(project_name):
    cwd = os.getcwd()
    project_dir = join(cwd, project_name)
    if not isdir(project_dir):
        os.makedirs(project_dir)
    file_dir = dirname(abspath(__file__))
    tpl_dir = join(file_dir, 'templates', 'project')

    for root, dirs, files in os.walk(tpl_dir, topdown=True):
        for f in files:
            relative_path = basename(root.replace(tpl_dir, ''))
            tpl_abs_file = join(root, f)
            if '__pycache__' in tpl_abs_file:
                continue
            project_abs_dir = join(project_dir, relative_path)
            if not isdir(project_abs_dir):
                os.makedirs(project_abs_dir)
            project_abs_file = join(project_abs_dir,  f.replace('.tpl', '.py'))
            content = ''
            with open(tpl_abs_file, 'r', 'utf-8') as f:
                content = f.read()
            if not project_abs_file.endswith('.json'):
                content = content.format(_capitalize_project_name=project_name.capitalize(), _project_name=project_name)
            with open(project_abs_file, 'w', 'utf-8') as f:
                f.write(content)

    click.echo('project %s created successfully' % project_name)


@main.command('newspider', short_help='create a new spider')
@click.argument('spider_name')
def newspider(spider_name):
    project_dir = os.getcwd()
    project_spiders_dir = join(project_dir, 'spiders')
    if not isdir(project_spiders_dir):
        click.echo('spiders directory not found, you should run this command inside project root', err=True)
        exit()
    file_dir = dirname(abspath(__file__))
    spider_tpl_file = join(file_dir, 'templates', 'spider', 'default.tpl')
    spider_file = join(project_spiders_dir, '{file}.{ext}'.format(file=spider_name, ext='py'))
    with open(spider_tpl_file, 'r', 'utf-8') as f1:
        content = f1.read().format(_capitalize_spider_name=spider_name.capitalize(), _spider_name=spider_name)
        with open(spider_file, 'w', 'utf-8') as f2:
            f2.write(content)
    click.echo('spider %s created successfully' % spider_name)


@main.command('start', short_help='start to run project')
@click.argument('project_path')
def start(project_path):
    cwd = os.getcwd()
    project_dir = realpath(normpath(join(cwd, project_path)))
    project_name = basename(project_dir)
    if not isdir(project_dir):
        click.echo('project root not found', err=True)
        exit()
    sys.path.append(dirname(project_dir))

    patan = Patan(join(project_dir, 'patan.json'))

    spiders_dir = join(project_dir, 'spiders')
    for mod_file in os.listdir(spiders_dir):
        mod_name = splitext(mod_file)[0]
        if mod_name == '__init__':
            continue
        mod_q_name = f'{project_name}.spiders.{mod_name}'
        module = import_module(mod_q_name)

        cls_list = [m[0] for m in inspect.getmembers(module, inspect.isclass) if m[1].__module__ == mod_q_name]
        for cls_name in cls_list:
            obj = getattr(module, cls_name)
            if isinstance(obj, type) and issubclass(obj, BaseSpider):
                patan.crawl(f'{mod_q_name}.{cls_name}')

    patan.start()


if __name__ == '__main__':
    main()
