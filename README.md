### Overview
Patan is a lightweight web crawling framework, used to crawl website pages and extract data from the pages. It can be first helpful tool for data analysis or data mining.
The core idea of Patan is inspired by [Scrapy](https://doc.scrapy.org/en/master/topics/architecture.html)

### Requirements

- Python 3.7+

### Contributing

- linter: flake8
- formatter: yapf

### Features

- Lightweight: pretty easy to learn and get started
- Fast: powered by asyncio and multiprocessing(TBD)
- Extensible: both spider and downloader is designed to be opened for custom middlewares

### Installation

```
pip install patan
```

### Get Started

#### create a new project

```
patan newproject projectname
```

#### generate a spider

```
cd projectname
patan newspider spidername
```

#### define where will your spider start

```python
start_urls = ['http://xxxx.html']
```

or you can override the start_requests method

```python
def start_requests(self):
        url_tpl = 'http://xxxx?page={}'
        for i in range(1, 200):
            url = url_tpl.format(i)
            yield Request(url=url, callback=self.parse, encoding=self.encoding)
```

#### create the item class

```python

@dataclass
class StockItem:
    field1: str
    field2: str
    # fieldn: type

```

#### finish the item pipeline

```python

class EastmoneyPipeline:

    def process_item(self, item, spider):
        # save item to database or files
        logger.info(item)

```

#### configure the item pipeline

```json
{
    "pipelines": {
        "eastmoney.pipelines.EastmoneyPipeline": 10
    }
}
```

#### configure the middlewares if you need it

```json
{
    "spider":{
        "middlewares": {
            "eastmoney.middlewares.EastmoneySpiderMiddleware": 200
        },
    },
    "downloader":{
        "middlewares": {
            "eastmoney.middlewares.EastmoneyDownloaderMiddleware": 200
        }
    }
}
```

#### finally, you're able to run the project now.

```
patan start [projectname|path-to-project]
```

### TODO

- [x] Settings File
- [x] Middlewares
- [x] Exception Handling
- [x] Throttle Control
- [x] Item Pipelines
- [x] Scaffolding CLI
- [ ] Multiprocessing
- [ ] Pause and Resume
- [ ] Statistics Data Collecting
- [ ] Web UI
- [ ] More Protocols Support

### Thanks

- [Scrapy](https://github.com/scrapy/scrapy)
- [aiohttp](https://github.com/aio-libs/aiohttp/)
- [glom](https://github.com/mahmoud/glom)