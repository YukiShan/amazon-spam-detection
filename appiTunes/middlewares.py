"""
Depth Spider Middleware for Amazon product and member pages

Requests for subsequent pages of the same product are regarded to be at the same depth
"""
from appiTunes.utils import APP_TYPE, DEV_TYPE, RWR_TYPE

__author__ = 'Shanshan'


from scrapy.spidermiddlewares.depth import DepthMiddleware
from scrapy.http import Request
import scrapy 
from scrapy import log
import random
from scrapy.conf import settings
# import logging

class iTunesDepthMiddleware(DepthMiddleware):
    def process_spider_output(self, response, result, spider):
        def _filter(request):
            if isinstance(request, Request):
                if (request.meta['id'], request.meta['type']) == (response.meta['id'], response.meta['type']):
                    depth = response.meta['depth']
                else:
                    depth = response.meta['depth'] + 1
                if depth > self.maxdepth:                    
                    log.msg(format="Ignoring link (depth > %(maxdepth)d): %(requrl)s ", level=log.DEBUG,
                            maxdepth=self.maxdepth, requrl=request.url)
                    # self.logger.debug("Ignoring link (depth > %d): %s " % (self.maxdepth,request.url))
                    return False
                # If we won't be able to crawl new items retrieved from reviews, then don't crawl the reviews
                if 'page' in request.meta and depth >= self.maxdepth:
                    log.msg(format="Ignoring review page request when items won't be crawled: depth == %(maxdepth)d %(itm_type)s %(itm_id)s",
                            level=log.DEBUG, maxdepth=self.maxdepth, itm_type=request.meta['type'], itm_id=request.meta['id'])
                    # self.logger.debug("Ignoring review page request when items won't be crawled: depth == %d %s %s" 
                    #     % (self.maxdepth, request.meta['type'], request.meta['id']))
                    return False
                request.meta['depth'] = depth
                if self.prio:
                    request.priority -= depth * self.prio
                if self.stats:
                    if self.verbose_stats:
                        self.stats.inc_value('request_depth_count/%s' % depth, spider=spider)
                    self.stats.max_value('request_depth_max', depth, spider=spider)
            return True

        # base case (depth=0)
        if self.stats and 'depth' not in response.meta:
            response.meta['depth'] = 0
            if self.verbose_stats:
                self.stats.inc_value('request_depth_count/0', spider=spider)

        return (r for r in result or () if _filter(r))


type_2_maxpage = {APP_TYPE: 'SPIDER_APP_MAX_NPAGE', RWR_TYPE: 'SPIDER_RWR_MAX_NPAGE'}


class iTunesMaxPageMiddleware(object):
    """
    Filters those request which ask for pages of reviews further than the max specified
    Assumes it is run after DepthMiddleware so the depth values are calculated
    """

    def __init__(self, settings):
        self.settings = settings

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_spider_output(self, response, result, spider):
        def _filter(request):
            # check if this is a request for pages of reviews
            if isinstance(request, Request) and 'page' in request.meta:
                settings_key = type_2_maxpage[request.meta['type']]
                if request.meta['page'] > self.settings[settings_key]:                   
                    log.msg(format='Skipping page (%(page_n)d > MAX_NPAGE): %(req_url)s', level=log.DEBUG,
                            page_n=request.meta['page'], req_url=request.url)
                    # self.logger.debug("Skipping page (%d > MAX_NPAGE): %s" % (request.meta['page'],request.url))
                    return False
            return True

        return (r for r in result or () if _filter(r))


class RandomUserAgent(object):

    def __init__(self,agents):
        self.agents = agents

    @classmethod
    def from_crawler(cls,crawler):
        return cls(crawler.settings.getlist('USER_AGENTS'))

    def process_request(self,request,spider):
        request.headers.setdefault('User-Agent', random.choice(self.agents))


class RandomProxy(object):
    def process_request(self, request, spider):
        request.meta['proxy'] = settings.get('HTTP_PROXY')


