# _*_ coding: utf-8 _*_

# import multiprocessing
from multiprocessing import Process, Queue
import asyncio
import logging
import sys

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s %(process)d [%(levelname)s] [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)


async def work(num):
    logger.info('before %d' % num)
    await asyncio.sleep(num)
    logger.info('after %d' % num)
    return num


def main(num):
    asyncio.run(work(num))
    logger.info('done asyncio loop %d' % num)


if __name__ == '__main__':
    for i in range(4):
        Process(target=main, args=(i,)).start()
