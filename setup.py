# _*_ coding: utf-8 _*_

import os
from codecs import open
from setuptools import setup
from setuptools import find_packages

version_info = {}
current_dir = os.path.abspath(os.path.dirname(__file__))
print(current_dir)
with open(os.path.join(current_dir, 'patan', '__version__.py'), 'r', 'utf-8') as f:
    exec(f.read(), version_info)

setup(
    name='Patan',
    version=version_info['__version__'],
    description='A lightweight web crawling framework',
    project_urls={'Source': 'https://github.com/20perline/patan'},
    url='https://github.com/20perline/patan',
    author='20perline',
    author_email='tlhk2@163.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={'console_scripts': ['patan = patan.cli:main']},
    install_requires=['aiohttp>=3.6.2', 'glom>=20.5.0', 'click>=6.7', 'aiohttp-sse-client>=0.2.1'],
    python_requires='>=3.7',
)

# local development
# pip install --upgrade .
