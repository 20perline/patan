# _*_ coding: utf-8 _*_

import sys
import json
import re
sys.path.append('../patan')
from patan.patan import Patan
from patan.spiders import BaseSpider
from patan.http.request import Request
from patan.settings import Settings


class EastmoneySpider(BaseSpider):

    name = 'eastmoney'

    def start_requests(self):
        url_tpl = 'http://17.push2.eastmoney.com/api/qt/clist/get?cb=jQuery1124047082144418373684_1588686141167&pn={}&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152&_=1588686141262'
        for i in range(1, 200):
            url = url_tpl.format(i)
            yield Request(url=url, callback=self.parse, encoding=self.encoding)

    def parse(self, response):
        body = re.sub(r'^jQuery[0-9_]+\((.*)\);$', r'\1', response.body)
        try:
            data = json.loads(body)
            for row in data['data']['diff']:
                yield {'code': row['f12'], 'name': row['f14']}
        except Exception as e:
            self.logger.error('parse item %s' % e)


if __name__ == '__main__':
    patan = Patan()
    patan.crawl(EastmoneySpider())
    patan.start()
