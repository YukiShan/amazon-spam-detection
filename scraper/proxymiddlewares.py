"""
Processing Scrapy requests using a random proxy from list to avoid IP ban and improve crawling speed.

"""

import re
import random
import base64
from scrapy import log
from scrapy.conf import settings

class RandomUserAgentMiddleware(object):
    def process_request(self, request, spider):
        ua  = random.choice(settings.get('USER_AGENT_LIST'))
        if ua:
            request.headers.setdefault('User-Agent', ua)

class ProxyMiddleware(object):
    def process_request(self, request, spider):
        request.meta['proxy'] = settings.get('HTTP_PROXY')


# class RandomUserAgent(object):
#     """
#     Randomly rotate user agents based on a list of predefined ones

#     """

#     def __init__(self, settings):
#         self.user_agents = settings['USER_AGENT_LIST']
#         fread = open(self.user_agents,'r')
       
#         self.agents = []
#         for line in fread.readlines():
#             self.agents.append(line[:-1])


#     @classmethod
#     def from_crawler(cls, crawler):
#         return cls(crawler.settings)

#     def process_request(self, request, spider):
#         #print("**************************" + random.choice(self.agents))
#         log.msg('Changing UserAgent...')
#         ua = random.choice(self.agents)
#         if ua:
#             request.headers.setdefault('User-Agent', random.choice(self.agents))
#         log.msg('>>>> UserAgent Changed.')


# class RandomProxy(object):
#     def __init__(self, settings):
#         self.proxy_list = settings['PROXY_LIST']
#         fin = open(self.proxy_list, 'r')

#         self.proxies = {}
#         for line in fin.readlines():
#             parts = re.match('(\w+://)(\w+:\w+@)?(.+)', line)
#             if not parts:
#                 continue

#             # Cut trailing @
#             if parts.group(2):
#                 user_pass = parts.group(2)[:-1]
#             else:
#                 user_pass = ''

#             self.proxies[parts.group(1) + parts.group(3)] = user_pass

#         fin.close()

#     @classmethod
#     def from_crawler(cls, crawler):
#         return cls(crawler.settings)

#     def process_request(self, request, spider):
#         # Don't overwrite with a random one (server-side state for IP)
#         if 'proxy' in request.meta:
#             return
        
#         log.msg('Changing IP address...')
#         proxy_address = random.choice(self.proxies.keys())
#         proxy_user_pass = self.proxies[proxy_address]

#         request.meta['proxy'] = proxy_address
#         if proxy_user_pass:
#             basic_auth = 'Basic ' + base64.encodestring(proxy_user_pass)
#             request.headers['Proxy-Authorization'] = basic_auth
#         log.msg('>>>> IP Address Changed.')

#     def process_exception(self, request, exception, spider):
#         proxy = request.meta['proxy']
#         log.msg('Removing failed proxy <%s>, %d proxies left' % (
#                     proxy, len(self.proxies)))
#         try:
#             del self.proxies[proxy]
#         except ValueError:
#             pass
