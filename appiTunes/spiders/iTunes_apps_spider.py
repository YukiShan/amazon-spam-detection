
__author__ = 'Shanshan'

import datetime
# from scrapy import log
import scrapy
import logging
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.utils.misc import arg_to_iter
from urlparse import urljoin
from appiTunes.items import App, RelatedApps, Review, Developer, Reviewer
import re
import socket
from scrapy.spiders import Spider
from appiTunes.utils import SingleValItemLoader, only_elem, only_elem_or_default, APP_TYPE, DEV_TYPE, RWR_TYPE
# from appiTunes.rank import get_rank
import pymongo
import json
import feedparser
import calendar
import csv

app_id_re = r'(?:(?:/id))(\d+)'
dev_id_re = r'(?:(?:/?id=))(\d+)'
star_rating_re = r'(\d+(?:\.\d+)?)\s+[stars|star]'
rvwer_rev_id_re = r'(?:(?:/?userReviewId=))(\d+)'
app_rvwer_id_re = re.compile(r'(?:(?:/id))(\d+)')
app_rvw_id_re = re.compile(r'(?:(?:mostRecent/))(\d+)')
app_page_re = re.compile(r'(?:(?:/page=))(\d+)')

app_countries = {
		'China':'cn',
		'United States':'us'
}

app_sortby = {
		'Most Recent':'mostRecent',
		'Most Helpful':'mostHelpful',
		'Most Favorable':'mostFavorable',
		'Most Critical':'mostCritical'
}

def _app_details_url(app_id):
		s = 'https://itunes.apple.com/lookup?id=%s' % app_id
		return s

def _app_rev_url(app_id, page=1, country_code = app_countries['United States'], sortby= app_sortby['Most Recent']):
		s = 'https://itunes.apple.com/%s/rss/customerreviews/page=%d/id=%s/sortBy=%s/xml' % (country_code, page, app_id, sortby)
		return s

def _rvwer_profile_url(rvwer_id, page=1):
		s = "https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewUsersUserReviews?userProfileId=%s&page=%d&sort=14"% (rvwer_id, page)
		return s

def _dev_profile_url(dev_id):
		s = 'https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewArtistSeeAll?cc=us&dkId=11&section=0&ids=%s&softwareType=iPhone'% dev_id
		return s

# def _dev_apps_iPad_url(dev_id, page=1):
# 		s = 'https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewArtistSeeAll?cc=us&dkId=11&section=1&ids=%s&softwareType=iPad'% dev_id
# 		return s

class AppleSpider(Spider):
		name = 'appiTunes'
		allowed_domains = ["itunes.apple.com"]

		def __init__(self, **kwargs):
				super(AppleSpider, self).__init__(**kwargs)        
				self.app_req_param = {
															APP_TYPE: (_app_details_url, self.parse_app_details_page),															
															DEV_TYPE: (_dev_profile_url, self.parse_dev_profile_page)														
															}

				self.rev_req_param = {
															APP_TYPE: (_app_rev_url, self.parse_app_rev_page),
															# RWR_TYPE: (_rvwer_profile_url, self.parse_rvwer_review_page)
															# RWR_TYPE: (_rvwer_profile_url, self.parse_rvwer_profile_page)																													
															}

		def _item_info_request(self, id_, type_, referrer):
				app_url_gen, cb = self.app_req_param[type_]
				req_meta = {'id': id_, 'type': type_, 'referrer': referrer}      
				return Request(app_url_gen(id_), callback=cb, meta=req_meta)

		def _rev_page_request(self, id_, type_, referrer=None, p=1):
				rev_url_gen, cb = self.rev_req_param[type_]
				req_meta = {'id': id_, 'type': type_, 'referrer': referrer, 'page': p}
				return Request(rev_url_gen(id_, p), callback=cb, meta=req_meta)

		def _successor_page_request(self, response):
				type_, id_, referrer_ = response.meta['type'], response.meta['id'], response.meta['referrer']
				next_p = response.meta['page'] + 1	
				# if type_ == APP_TYPE:				
				return self._rev_page_request(id_, type_, referrer_, next_p)
				# referrer_ = response.meta['referrer']
				# return self._item_info_request(id_, type_, referrer_, next_p)				


		def start_requests(self):
				"""
				read seed data from serverSeeds.csv

				"""
				# reqs = []

				# while(True):
				# 	try:
				# 		req = self._item_info_request('1111479706', APP_TYPE, referrer=None)
				# 	except KeyError:
				# 		raise ValueError("App with ID %s on iTunes is not available currently." % app_id)
				# 	reqs += arg_to_iter(req)
				# 	break
				# return reqs
				
				settings = self.crawler.settings
				reqs = []

				with open(settings['SPIDER_SEED_FILENAME'], 'r') as read_file:
					reader = csv.DictReader(read_file)
					for seed in reader:         
						app_platform = seed['Platform']
						app_id = seed['ID']	
						# dev_id = seed['ID']					             
						try:
							if app_platform == 'App store':								                    
								# req = self._item_info_request(app_id, APP_TYPE, referrer=None)
								req = self._rev_page_request(app_id, APP_TYPE)
								# req = self._item_info_request(dev_id, DEV_TYPE, referrer=None)
						except KeyError:
							raise ValueError("App with ID %s on iTunes is not available currently." % app_id)
						reqs += arg_to_iter(req)
				return reqs				


				# settings = self.crawler.settings
				# reqs = []
				
				# connection = pymongo.MongoClient('localhost',27017)
				# db = connection[settings['MONGODB_APP_TASK_DB']]
				# cursor = db['appPaidTasks'].find({})
				# # ###########
				# # tmp_count = 0
				# # ###########
				# for seed in cursor:					
				# 	app_platform = seed['app_platform']
				# 	app_id = seed['app_id']
				# 	try:
				# 		if app_platform == 'App store':
				# 			# print itm_id
				# 			# print 'before request'
				# 			req = self._item_info_request(app_id, APP_TYPE, referrer=None)  
				# 			# req = self._item_info_request('628228162', APP_TYPE, referrer=None)  
				# 			# print 'after request'     			
				# 	except KeyError:
				# 		raise ValueError("App with ID %s in %s platform is not available currently." % (app_id, app_platform))
				# 	reqs += arg_to_iter(req)
				# 	# ###########
				# 	# tmp_count += 1
				# 	# if tmp_count > 0:
				# 	# 	break
				# 	# ###########
				# cursor.close()        
				# return reqs


		def parse_app_details_page(self, response):
				"""
				Parses app basic info in app store
				"""

				# settings = self.crawler.settings
				# self.logger.info('Parsing app info: %s' % response.meta['id'])
				# context = json.loads(response.body)['results']
				# if not context:
				# 	self.logger.info("App with ID %s in App Store is not available currently." % (response.meta['id']))
				# 	return	
				# app_context = context[0]
				
				# # app = SingleValItemLoader(item=App(), response=response) 
				# app_id = response.meta['id'] 				
				# app.add_value('id', app_id)
				# app_referrer = response.meta['referrer']   
				# app.add_value('referrer', app_referrer)				
				# app.add_value('app_name', app_context['trackName'])        
				# app.add_value('countries', 'us')
				# if app_context['kind'] == 'mac-software':
				# 	app.add_value('iphone', 0)
				# 	app.add_value('ipad', 0)
				# 	app.add_value('osx', 1)
				# else:
				# 	app.add_value('iphone', 1)
				# 	app.add_value('ipad', 1)
				# 	app.add_value('osx', 0)       	
				# app.add_value('description', app_context['description'])       	
				# app.add_value('image_url', app_context['artworkUrl60'])       	
				# app.add_value('app_store_url', app_context['trackViewUrl'])       	
				# app.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
				# app.add_value('bundleId', app_context['bundleId'])  
				# app.add_value('developer_id', app_context['artistId'])       	
				# app.add_value('developer_name', app_context['sellerName'])       	
				# app.add_value('release_date', app_context['releaseDate'])       	
				# app.add_value('price', app_context['price'])       	
				# app.add_value('genres', app_context['genres'])  
				# app.add_value('main_cat', app_context['primaryGenreName'])     	  	
				# app.add_value('content_rating_age_group', app_context['trackContentRating'])       	   	
				# app.add_value('languages', app_context['languageCodesISO2A'])       	
				# app.add_value('cur_ver_release_date', app_context['currentVersionReleaseDate'])       	
				# app.add_value('app_type', app_context['wrapperType'])       	
				# app.add_value('version', app_context['version'])       	     	
				# app.add_value('currency', app_context['currency'])
				# app.add_value('min_os_version', app_context['minimumOsVersion'])  
				# try:
				# 	app.add_value('enabled', app_context['isVppDeviceBasedLicensingEnabled'])	
				# except KeyError:
				# 	self.logger.info('Index does not exist!') 
				# 	app.add_value('enabled', 0)   
				# try:
				# 	app.add_value('avg_rating_for_cur_version', app_context['averageUserRatingForCurrentVersion'])
				# except KeyError:
				# 	self.logger.info('Index does not exist!')
				# 	app.add_value('avg_rating_for_cur_version', 0)       	
				# try: 
				# 	app.add_value('rating_count_for_cur_version', app_context['userRatingCountForCurrentVersion'])
				# except KeyError:
				# 	self.logger.info('Index does not exist!')
				# 	app.add_value('rating_count_for_cur_version', 0)       	
				# try:
				# 	app.add_value('avg_rating', app_context['averageUserRating'])
				# except KeyError:
				# 	self.logger.info('Index does not exist!')
				# 	app.add_value('avg_rating', 0)       	
				# try:
				# 	app.add_value('rating_count', app_context['userRatingCount'])
				# except KeyError:
				# 	self.logger.info('Index does not exist!')
				# 	app.add_value('rating_count', 0)
				# try:
				# 	app.add_value('release_notes', app_context['releaseNotes'])
				# except KeyError:
				# 	self.logger.info('Index does not exist!')
				# 	app.add_value('release_notes', 0)       	  	 
				
				# yield app.load_item()				

				#yield the app related page.
				# yield Request(app._values['app_store_url'], callback=self.parse_app_related_page, 
				# 	meta= {'id': app_id, 'type': APP_TYPE, 'referrer': app_id})

				# yield Request(app_context['trackViewUrl'], callback=self.parse_app_related_page, 
				# 	meta= {'id': app_id, 'type': APP_TYPE, 'referrer': app_id})

				# # yield the app reviews page
				# yield self._rev_page_request(app_id, APP_TYPE)


		def parse_app_rev_page(self, response):
				"""
				Parses at most 500 app reviews in app store
				"""
				# Start parsing this page
				self.logger.info('Parsing app reviews: %s  p%d' % (response.meta['id'], response.meta['page']))
				settings = self.crawler.settings  
				feed = feedparser.parse(response.url)		
				if not feed.entries:
						self.logger.info('Get nothing from %s'% response.url)
						return 				
				# ###########
				# tmp_count = 0
				# ###########				
				for entry in feed.entries[1:]:
						review = SingleValItemLoader(item=Review(), response=response)
						review.add_value('id', app_rvw_id_re.findall(entry['id'])[0])
						review.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
						review.add_value('title', entry['title'])
						review.add_value('app_id', response.meta['id'])
						review.add_value('comment', entry['content'][0]['value'])
						review.add_value('reviewer_name', entry['author'])						
						review.add_value('reviewer_id', app_rvwer_id_re.findall(entry['authors'][0]['href'])[0])
						review.add_value('starRating', entry['im_rating'])
						review.add_value('version', entry['im_version'])
						review.add_value('vote', entry['im_votecount'])
						review.add_value('country', 'us')
						review.add_value('updated', datetime.datetime.fromtimestamp
							(int(calendar.timegm(entry['updated_parsed']))).strftime(settings['TS_FMT']))												
						# print(review._values['updated'])						

						yield review.load_item()

						# yield the reviewer						
						# yield self._rev_page_request(review._values['reviewer_id'], RWR_TYPE, referrer=response.meta['id'])
						# yield self._rev_page_request('747414921', RWR_TYPE, referrer=response.meta['id'])
						
						# ###########
						# tmp_count += 1
						# if tmp_count > 1:
						# 	break
						# ###########
				# request subsequent pages to be downloaded
				# Find out the number of review pages
				noPages = int(app_page_re.findall(feed.feed['links'][3]['href'])[0])
				if response.meta['page'] < noPages:
						# print(">>>>>>>test from here 210 <<<<<<<<<<<")						
						yield self._successor_page_request(response)


		def parse_rvwer_profile_page(self, response):
				"""
				Parses review info by the reviewer in app store
				"""

				self.logger.info('Parsing review info by the same reviewer: %s  p%d' % (response.meta['id'], response.meta['page']))
				hxs = Selector(response)
				settings = self.crawler.settings
				# print(">>>>>>>test from here 210 <<<<<<<<<<<")						
				# print(response.body)
				reviewer = SingleValItemLoader(item=Reviewer(), response=response)
				reviewer.add_value('id', response.meta['id'])
				reviewer.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
				reviewer.add_value('referrer', response.meta['referrer'])
				rvwer_page_title = only_elem_or_default(hxs.xpath('//body//div[@class="main-title"]/text()').extract())											
				startIdx = rvwer_page_title.find('by ')
				rvwer_name = rvwer_page_title[startIdx+3:]
				reviewer.add_value('reviewer_name', rvwer_name)
				app_ids_reviewed = hxs.xpath('//body//a[@class="artwork-link"]/@href').re(app_id_re)
				reviewer.add_value('nApps_rvwed', len(app_ids_reviewed))
				reviewer.add_value('app_ids_rvwed', app_ids_reviewed)
				rev_ratings_str_list = hxs.xpath('//body//div[@class="rating"]/@aria-label').extract()	
				# print(">>>>>>>test from here 210 <<<<<<<<<<<")						
				# print(rev_ratings_str_list)				
				rev_ratings = []
				if len(rev_ratings_str_list)>1:					
					for rev_ratings_str in rev_ratings_str_list:
						rev_rating =rev_ratings_str.split(" ")[0]
						rev_ratings.append(rev_rating)
				else:
					rev_ratings =rev_ratings_str_list[0].split(" ")[0]
				reviewer.add_value('review_ratings', rev_ratings)
				rev_dates = hxs.xpath('//body//div[@class="review-date"]/text()').extract()
				reviewer.add_value('review_dates', rev_dates)
				app_versions_reviewed = hxs.xpath('//body//button/@bundle-short-version').extract()
				reviewer.add_value('app_versions_rvwed', app_versions_reviewed)
				app_developerIds_rvwed = hxs.xpath('//body//li[@class="artist"]/a/@href').re(app_id_re)
				reviewer.add_value('app_devIds_rvwed', app_developerIds_rvwed)
				app_cats_rvwed = hxs.xpath('//body//li[@class="genre"]/text()').extract()
				try:
					reviewer.add_value('app_cats_rvwed', app_cats_rvwed)						
				except KeyError:
					self.logger.info('Index does not exist!') 
					reviewer.add_value('app_cats_rvwed', ' ')				
				app_releaseDates_str1_rvwed = hxs.xpath('//body//li[@class="release-date"]/span/text()').extract()
				app_releaseDates_str2_rvwed = hxs.xpath('//body//li[@class="release-date"]/text()').extract()
				app_releaseDates_str_rvwed = zip(app_releaseDates_str1_rvwed, app_releaseDates_str2_rvwed)
				app_releaseDates_rvwed = []
				for itm in app_releaseDates_str_rvwed:
					app_releaseDates_rvwed.append(''.join(itm))							
				reviewer.add_value('app_releaseDates_rvwed', app_releaseDates_rvwed)
				app_review_titles = hxs.xpath('//body//div[@class="title-text"]/text()').extract()
				reviewer.add_value('app_review_titles', app_review_titles)
				app_review_txts = hxs.xpath('//body//div[@class="review-block"]/p/text()').extract()
				reviewer.add_value('app_review_txts', app_review_txts)				
				yield reviewer.load_item()					
				
				# Find out current page and total number of review pages
				curPageNum = int(only_elem(hxs.xpath('//body//div[@class="paginated-content"]/@page-number').extract()))
				noPages = int(only_elem(hxs.xpath('//body//div[@class="paginated-content"]/@total-number-of-pages').extract()))
				if noPages == 1 and len(app_ids_reviewed) == 1:
					# assert only_elem(app_ids_reviewed) == response.meta['referrer']
					self.logger.info(r'Aborting unavailable reviewer page: %s' % response.url)
					return

				for app_id in app_ids_reviewed:					
					yield self._item_info_request(str(app_id), APP_TYPE, referrer=response.meta['id'])	

				if curPageNum == noPages:
					self.logger.info(r'Finishing crawling reviewer pages: %s' % response.url)
					return
				# request subsequent review pages to be downloaded				
				if response.meta['page'] < noPages:
						yield self._successor_page_request(response)			


		def parse_app_related_page(self, response):
				"""
				Parses apps from an app related page in app store
				"""

				self.logger.info('Parsing apps related to: %s' % response.meta['id'])
				hxs = Selector(response)				
				apps_related = SingleValItemLoader(item=RelatedApps(), response=response)
				apps_related.add_value('id', response.meta['referrer'])

				apps_ids_bought = hxs.xpath('//body//div[contains(h2/text(), "Customers Also Bought")]/following-sibling::div[@num-items="10"]//a[@class="artwork-link"]/@href').re(app_id_re)				

				apps_related.add_value('nApps_related', len(apps_ids_bought))				
				apps_related.add_value('app_ids_related', apps_ids_bought)
				# print(">>>>>>>test from here 210 <<<<<<<<<<<")						
				# print(apps_related._values['app_ids_related'])
				yield apps_related.load_item()					
				
				# dev_id = hxs.xpath('//body//h4[contains(text(), "More by")]/a/@href').re(dev_id_re)
				# if dev_id:	
				# 	# print(">>>>>>> crawling developer now <<<<<<<<<<<")					
				# 	yield self._item_info_request(only_elem(dev_id), DEV_TYPE, referrer=response.meta['referrer'])
				# 	# yield self._item_info_request(only_elem(dev_id), DEV_IPAD_TYPE, referrer=response.meta['referrer'])
				
				# if apps_ids_bought: 
				# 	for app_id in apps_ids_bought:											
				# 		yield self._item_info_request(str(app_id), APP_TYPE, referrer=response.meta['referrer'])
				

		def parse_dev_profile_page(self, response):
				"""
					Parses apps from same developer in app store
				"""
				self.logger.info('Parsing apps by the same developer: %s' % response.meta['id'])
				settings = self.crawler.settings  
				hxs = Selector(response)
				# print(">>>>>>>test from here 210 <<<<<<<<<<<")						
				# print(response.body)

				developer = SingleValItemLoader(item=Developer(), response=response)
				dev_name_title = only_elem_or_default(hxs.xpath('//body//h1//text()').extract()).lower()
				startIdx = dev_name_title.find('by ')
				name = dev_name_title[startIdx+3:]
				developer.add_value('name', name)				
				developer.add_value('id', response.meta['id'])
				developer.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
				developer.add_value('referrer', response.meta['referrer'])
				app_ids = hxs.xpath('//body//a[@class="artwork-link"]/@href').re(app_id_re)				
				# if app_ids:					
				developer.add_value('nApps_deved', len(app_ids))				
				developer.add_value('app_ids_deved', app_ids)
				yield developer.load_item()

				# if len(app_ids) == 1:
				# 	assert only_elem(app_ids) == response.meta['referrer']
				# 	self.logger.info(r'Aborting unavailable developer page: %s' % response.url)
				# 	return

				# for app_id in app_ids:
				# 	yield self._item_info_request(str(app_id), APP_TYPE, referrer=response.meta['id'])	
				# else:
				# 	yield developer.load_item()
