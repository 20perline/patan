# _*_ coding: utf-8 _*_
import re
import json
from patan.spiders import BaseSpider
from patan.http.request import Request
from ..items import StockItem


class EastmoneySpider(BaseSpider):

    name = 'eastmoney'

    def start_requests(self):
        url_tpl = 'http://17.push2.eastmoney.com/api/qt/clist/get?cb=jQuery1124047082144418373684_1588686141167&pn={}&pz=20&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23&fields=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152&_=1588686141262'
        for i in range(1, 200):
            url = url_tpl.format(i)
            yield Request(url=url, callback=self.parse_list, encoding=self.encoding)

    def parse_list(self, response):
        body = re.sub(r'^jQuery[0-9_]+\((.*)\);$', r'\1', response.body)
        try:
            data = json.loads(body)
        except Exception as e:
            self.logger.error('parse list %s' % e)
        if data is None:
            return
        item_url_tpl = 'https://2.push2.eastmoney.com/api/qt/ulist/sse?invt=3&pi=0&pz=3&mpi=2000&secids={}.{}&ut=6d2ffaa6a585d612eda28417681d58fb&fields=f12,f13,f19,f14,f139,f148,f2,f4,f1,f125,f18,f3,f152,f88,f153,f89,f90,f91,f92,f94,f95,f97,f98,f99&po=1'
        for row in data['data']['diff']:
            item = StockItem()
            item.code = row['f12']
            item.name = row['f14']
            item_owner = 1 if item.code[0] == '6' else 0
            url = item_url_tpl.format(item_owner, item.code)
            yield Request(url=url, callback=self.parse_item, meta=dict(is_sse=True), cb_kwargs=dict(item=item), encoding=self.encoding)

    def parse_item(self, response, item):
        try:
            data = json.loads(response.body)
        except Exception as e:
            self.logger.error('parse item %s' % e)
        item.ddx = data['data']['diff']['0']['f88']
        self.logger.info(item)
