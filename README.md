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

### TODO

- [x] Settings File
- [x] Middlewares
- [x] Exception Handling
- [x] Throttle Control
- [x] Item Pipelines
- [ ] Scaffolding CLI
- [ ] Multiprocessing
- [ ] Pause and Resume
- [ ] Statistics Data Collecting
- [ ] Web UI
- [ ] More Protocols Support

### Thanks

- [Scrapy](https://github.com/scrapy/scrapy)
- [aiohttp](https://github.com/aio-libs/aiohttp/)
- [glom](https://github.com/mahmoud/glom)