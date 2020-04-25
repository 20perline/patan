# _*_ coding: utf-8 _*_
import logging
from logging import NullHandler
import sys

logging.getLogger(__name__).addHandler(NullHandler())
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s %(process)d [%(levelname)s] [%(name)s] %(message)s'
)
