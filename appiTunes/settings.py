# -*- coding: utf-8 -*-

# Scrapy settings for apple project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
import os
from os import path

BOT_NAME = 'iTunes Spider'

USER_AGENTS = [
	'iTunes/10.5.3 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20'
	'iTunes/10.5.3 (Windows; Microsoft Windows 7 x64 Ultimate Edition Service Pack 1 (Build 7601)) AppleWebKit/534.52.7'
	'iTunes/10.5.3 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)'
	'iTunes/10.5.3 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11'
	'iTunes/10.5.3 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER'
	'iTunes/10.5.3 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6'
	'iTunes/10.5.3 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10'
	'iTunes/10.5.3 (Windows NT 6.1; WOW64) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.36 Safari/535.7'
	'iTunes/10.5.3 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'
	'iTunes/10.5.3 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52'
	'iTunes/10.5.3 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER'
	'iTunes/10.5.3 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10'
	'iTunes/10.5.3 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
	'iTunes/10.5.3 Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0'
	'iTunes/10.5.3 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre'
	'iTunes/10.5.3 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5'
	'iTunes/10.5.3 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1'
	'iTunes/10.5.3 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)'
	'iTunes/10.5.3 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)'
	'iTunes/10.5.3 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5'
	'iTunes/10.5.3 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0'
]

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
LOG_LEVEL = 'INFO'
DOWNLOAD_DELAY = 0.25
RANDOMIZE_DOWNLOAD_DELAY = True

# Retry many times since proxies often fail
RETRY_TIMES = 10
# Retry on most error codes
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]

# Use Tor proxy
HTTP_PROXY ='http://127.0.0.1:8123'

DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None, 
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,   
    'appiTunes.middlewares.RandomUserAgent': 400,
    # 'appiTunes.middlewares.RandomProxy':410,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
}

# Spider
SPIDER_MODULES = ['appiTunes.spiders']
NEWSPIDER_MODULE = 'appiTunes.spiders'
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.depth.DepthMiddleware': None,
    'appiTunes.middlewares.iTunesDepthMiddleware': 901,
    'appiTunes.middlewares.iTunesMaxPageMiddleware': 902,
}

# Pipeline
ITEM_PIPELINES = {  'appiTunes.pipelines.AppleMongoDBPipeline': 800,
					# 'appiTunes.pipelines.AppleMySQLDBPipeline': 800, 
                  }

# IO
TS_FMT = "%Y-%m-%d %H:%M:%S"
PROJECT_PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
DATA_SET_DIR = path.join(PROJECT_PATH, 'io')
SPIDER_SEED_FILENAME = path.join(DATA_SET_DIR, 'lastApps.csv')

# Depth
DEPTH_LIMIT = 3
DEPTH_PRIORITY = 1
DEPTH_STATS_VERBOSE = True

SPIDER_APP_MAX_NPAGE = 10
# SPIDER_DEV_MAX_NPAGE = 10
SPIDER_RWR_MAX_NPAGE = 100

#Mongo Database
MONGODB_SERVER = "localhost"
MONGODB_PORT = 27017
MONGODB_APP_TASK_DB = "microworkersAppTasks"
MONGODB_APP_TASK_COLLECTION = "appPaidTasks"

MONGODB_ITUNES_APP_DB = "revsFrmLastApps_0227"
MONGODB_APP_COLLECTION = "apps"
MONGODB_REVIEW_COLLECTION = "reviews"
MONGODB_DEV_COLLECTION = "developers"
MONGODB_RWR_COLLECTION = "reviewers"

MONGODB_ITUNES_RAND_APP_DB = "randAppsFrmiTunes"
MONGODB_RAND_APP_COLLECTION = "apps"
MONGODB_RAND_REVIEW_COLLECTION = "reviews"
MONGODB_RAND_DEV_COLLECTION = "developers"
MONGODB_RAND_RWR_COLLECTION = "reviewers"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'apple (+http://www.yourdomain.com)'



# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'apple.middlewares.MyCustomSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'apple.middlewares.MyCustomDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'apple.pipelines.SomePipeline': 300,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
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
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
