# Scrapy settings for AmazonScraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
import os
from os import path


BOT_NAME = 'The Mighty Amazon Scraper'

USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.36 Safari/535.7',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64; rv:16.0) Gecko/16.0 Firefox/16.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/534.55.3 (KHTML, like Gecko) Version/5.1.3 Safari/534.53.10'
]
# USER_AGENT = 'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)'
# USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'
# USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11'
COOKIES_ENABLED = False
ROBOTSTXT_OBEY = False
LOG_LEVEL = 'INFO'

# Pipeline
ITEM_PIPELINES = {'scraper.pipelines.DuplicatesPipeline': 300,  
                  'scraper.pipelines.MongoDBPipeline': 800,
                  'scraper.pipelines.InstantJsonExportPipeline': 1000,
                  }

# IO
TS_FMT = "%Y-%m-%d %H:%M:%S"
PROJECT_PATH = os.path.split(os.path.dirname(os.path.abspath(__file__)))[0]
DATA_SET = 'same_cat_v2'
DATA_SET_DIR = path.join(PROJECT_PATH, 'io', DATA_SET)

# Scheduler
#DOWNLOAD_DELAY = 0.2
SCHEDULER_DISK_QUEUE = 'scrapy.squeues.PickleFifoDiskQueue'
SCHEDULER_MEMORY_QUEUE = 'scrapy.squeues.FifoMemoryQueue'

# Spider
SPIDER_MODULES = ['scraper.spiders']
NEWSPIDER_MODULE = 'scraper.spiders'
SPIDER_MIDDLEWARES = {
    'scrapy.spidermiddlewares.depth.DepthMiddleware': None,
    'scraper.middlewares.AmazonDepthMiddleware': 901,
    'scraper.middlewares.AmazonMaxPageMiddleware': 902,
}
# SPIDER_SEED_FILENAME = path.join('/Users/ssli/Documents/Research/crowdsourceScraper/', 'io', DATA_SET, 'seed.csv')
SPIDER_SEED_FILENAME = path.join(DATA_SET_DIR, 'seed.csv')
SPIDER_PROD_MAX_NPAGE = 30
SPIDER_MEMBER_MAX_NPAGE = 30
SPIDER_MAX_SAME_CAT = 5
SPIDER_MAX_SAME_MANUFACT = 5

# Depth
DEPTH_LIMIT = 2
DEPTH_PRIORITY = 1
DEPTH_STATS_VERBOSE = True

DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True

#Database
MONGODB_SERVER = "localhost"
MONGODB_PORT = 27017
MONGODB_DST_DB = "amazonSpamReview"
MONGODB_SRC_DB = "rapidworkersAmazonTasks"
MONGODB_MEMBER_COLLECTION = "members"
MONGODB_PRODUCT_COLLECTION = "products"
MONGODB_REVIEW_COLLECTION = "reviews"

#Random proxies

# Retry many times since proxies often fail
RETRY_TIMES = 10
# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]

# PROXY_LIST = path.join(DATA_SET_DIR, 'proxyList.txt')

# USER_AGENT_LIST = path.join(DATA_SET_DIR, 'user_Agents.txt')

# HTTP_PROXY = 'http://127.0.0.1:8123'

# DOWNLOADER_MIDDLEWARES = {
	# 'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
	# 'scraper.proxymiddlewares.RandomUserAgentMiddleware': 400,
 #    'scraper.proxymiddlewares.ProxyMiddleware': 410,
 #    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    # 'scrapy.contrib.downloadermiddleware.httpproxy.HttpProxyMiddleware': 110,
    # 'scrapy_crawlera.CrawleraMiddleware': 300
# }

# CRAWLERA_ENABLED = True
# CRAWLERA_USER = '6a577e6294f14b6caf0cb0a4af485087'
# CRAWLERA_PASS = ''
# 
CONCURRENT_REQUESTS = 32
CONCURRENT_REQUESTS_PER_DOMAIN = 32
AUTOTHROTTLE_ENABLED = False
DOWNLOAD_TIMEOUT = 300