# Scrapy settings for technolife project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os
from urllib.parse import quote

BOT_NAME = "technolife"

SPIDER_MODULES = ["technolife.spiders"]
NEWSPIDER_MODULE = "technolife.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "technolife (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

CONCURRENT_REQUESTS = 10
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True


AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "technolife.middlewares.TechnolifeSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "technolife.middlewares.TechnolifeDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    "technolife.pipelines.TechnolifePipeline": 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value


REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"


SCHEDULER = "scrapy_redis.scheduler.Scheduler"
DUPEFILTER_CLASS = "technolife.dupefilter.NoDupeFilter"
SCHEDULER_QUEUE_CLASS = 'scrapy_redis.queue.FifoQueue'
MAX_IDLE_TIME_BEFORE_CLOSE = 3600 * 30

ITEM_PIPELINES = {
   'scrapy_redis.pipelines.RedisPipeline': 200,
}


ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST")
ELASTICSEARCH_PORT = os.getenv("ELASTICSEARCH_PORT")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_PRODUCT_INDEX = os.getenv("ELASTICSEARCH_PRODUCT_INDEX", "products")

LOG_LEVEL = os.getenv("LOG_LEVEL", "ERROR")
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = os.getenv("REDIS_PORT") or "6379"
REDIS_USERNAME = os.getenv("REDIS_USERNAME", "default")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = os.getenv("REDIS_CRAWLER_DB", "0")

if REDIS_PASSWORD:
    REDIS_URL = (
        f"redis://{quote(REDIS_USERNAME, safe='')}:{quote(REDIS_PASSWORD, safe='')}"
        f"@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
    )
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
