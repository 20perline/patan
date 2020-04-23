import shutil
import requests
import time
import os


def download_img(url, dir=None):
    response = requests.get(url, stream=True)
    milliseconds = int(round(time.time() * 1000))
    with open(os.path.join(dir, '{}.jpg'.format(milliseconds)), 'wb') as output_file:
        shutil.copyfileobj(response.raw, output_file)
    del response
