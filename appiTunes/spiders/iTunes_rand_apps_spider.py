
__author__ = 'Shanshan'

import datetime
# from scrapy import log
import scrapy
import logging
from scrapy.http import FormRequest, Request
from scrapy.selector import Selector
from scrapy.utils.misc import arg_to_iter
from urlparse import urljoin
from appiTunes.items import RandApp, RandRelatedApps, RandReview, RandDeveloper, RandReviewer
import re
from scrapy.spiders import Spider
from appiTunes.utils import SingleValItemLoader, only_elem, only_elem_or_default, APP_TYPE, DEV_TYPE, RWR_TYPE
# from appiTunes.rank import get_rank
import pymongo
import json
import feedparser
import calendar

_NEXT_PAGE_VALUE = 5
app_id_re = r'(?:(?:/id))(\d+)'
dev_id_re = r'(?:(?:/?id=))(\d+)'
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

def _app_details_url(app_id, page=1):
		s = 'https://itunes.apple.com/lookup?id=%s' % app_id
		return s

def _app_rev_url(app_id, page=1, country_code = app_countries['United States'], sortby= app_sortby['Most Recent']):
		s = 'https://itunes.apple.com/%s/rss/customerreviews/page=%d/id=%s/sortBy=%s/xml' % (country_code, page, app_id, sortby)
		return s

def _rvwer_profile_url(rvwer_id, page=1):
		s = "https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewUsersUserReviews?userProfileId=%s&page=%d&sort=14"% (rvwer_id, page)
		return s

def _dev_apps_iPhone_url(dev_id, page=1):
		s = 'https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewArtistSeeAll?cc=us&dkId=11&section=0&ids=%s&softwareType=iPhone'% dev_id
		return s

def _dev_apps_iPad_url(dev_id, page=1):
		s = 'https://itunes.apple.com/WebObjects/MZStore.woa/wa/viewArtistSeeAll?cc=us&dkId=11&section=1&ids=%s&softwareType=iPad'% dev_id
		return s

class AppleSpider(Spider):
		name = 'randAppiTunes'
		allowed_domains = ["itunes.apple.com"]

		def __init__(self, **kwargs):
				super(AppleSpider, self).__init__(**kwargs)        
				self.app_req_param = {
															APP_TYPE: (_app_details_url, self.parse_app_details_page),
															DEV_IPHONE_TYPE: (_dev_apps_iPhone_url, self.parse_dev_profile_page),
															DEV_IPAD_TYPE: (_dev_apps_iPad_url, self.parse_dev_profile_page),
															RWR_TYPE: (_rvwer_profile_url, self.parse_rvwer_profile_page)
															}

				self.rev_req_param = {
															APP_TYPE: (_app_rev_url, self.parse_app_rev_page)																													
															}

		def _item_info_request(self, id_, type_, referrer, p=1):
				app_url_gen, cb = self.app_req_param[type_]
				req_meta = {'id': id_, 'type': type_, 'referrer': referrer, 'page': p}      
				return Request(app_url_gen(id_, p), callback=cb, meta=req_meta)

		def _rev_page_request(self, id_, type_, p=1):
				rev_url_gen, cb = self.rev_req_param[type_]
				req_meta = {'id': id_, 'type': type_, 'page': p}
				return Request(rev_url_gen(id_, p), callback=cb, meta=req_meta)

		def _successor_page_request(self, response):
				type_, id_ = response.meta['type'], response.meta['id']
				next_p = response.meta['page'] + 1	
				if type_ == APP_TYPE:			
					return self._rev_page_request(id_, type_, next_p)
				referrer_ = response.meta['referrer']
				return self._item_info_request(id_, type_, referrer_, next_p)				


		def start_requests(self):
				"""
				read seed data from database

				"""
				reqs = []

				while(True):
					try:
						req = self._item_info_request('1111479706', APP_TYPE, referrer=None)
					except KeyError:
						raise ValueError("App with ID %s on iTunes is not available currently." % app_id)
					reqs += arg_to_iter(req)
					break
				return reqs


		def parse_app_details_page(self, response):
				"""
				Parses app basic info in app store
				"""

				settings = self.crawler.settings
				self.logger.info('Parsing app info: %s' % response.meta['id'])
				context = json.loads(response.body)['results']
				if not context:
					self.logger.info("App with ID %s in App Store is not available currently." % (response.meta['id']))
					return	
				app_context = context[0]
				
				rand_app = SingleValItemLoader(item=RandApp(), response=response) 
				app_id = response.meta['id'] 				
				rand_app.add_value('id', app_id)
				app_referrer = response.meta['referrer']   
				rand_app.add_value('referrer', app_referrer)				
				rand_app.add_value('app_name', app_context['trackName'])        
				rand_app.add_value('countries', 'us')
				if app_context['kind'] == 'mac-software':
					rand_app.add_value('iphone', 0)
					rand_app.add_value('ipad', 0)
					rand_app.add_value('osx', 1)
				else:
					rand_app.add_value('iphone', 1)
					rand_app.add_value('ipad', 1)
					rand_app.add_value('osx', 0)       	
				rand_app.add_value('description', app_context['description'])       	
				rand_app.add_value('image_url', app_context['artworkUrl60'])       	
				rand_app.add_value('app_store_url', app_context['trackViewUrl'])       	
				rand_app.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
				rand_app.add_value('bundleId', app_context['bundleId'])  
				rand_app.add_value('developer_name', app_context['artistId'])       	
				rand_app.add_value('developer_name', app_context['sellerName'])       	
				rand_app.add_value('release_date', app_context['releaseDate'])       	
				rand_app.add_value('price', app_context['price'])       	
				rand_app.add_value('genres', app_context['genres'])  
				rand_app.add_value('main_cat', app_context['primaryGenreName'])     	  	
				rand_app.add_value('content_rating_age_group', app_context['trackContentRating'])       	   	
				rand_app.add_value('languages', app_context['languageCodesISO2A'])       	
				rand_app.add_value('cur_ver_release_date', app_context['currentVersionReleaseDate'])       	
				rand_app.add_value('app_type', app_context['wrapperType'])       	
				rand_app.add_value('version', app_context['version'])       	     	
				rand_app.add_value('currency', app_context['currency'])
				rand_app.add_value('min_os_version', app_context['minimumOsVersion'])  
				try:
					rand_app.add_value('enabled', app_context['isVppDeviceBasedLicensingEnabled'])	
				except KeyError:
					self.logger.info('Index does not exist!') 
					rand_app.add_value('enabled', 0)   
				try:
					rand_app.add_value('avg_rating_for_cur_version', app_context['averageUserRatingForCurrentVersion'])
				except KeyError:
					self.logger.info('Index does not exist!')
					rand_app.add_value('avg_rating_for_cur_version', 0)       	
				try: 
					rand_app.add_value('rating_count_for_cur_version', app_context['userRatingCountForCurrentVersion'])
				except KeyError:
					self.logger.info('Index does not exist!')
					rand_app.add_value('rating_count_for_cur_version', 0)       	
				try:
					rand_app.add_value('avg_rating', app_context['averageUserRating'])
				except KeyError:
					self.logger.info('Index does not exist!')
					rand_app.add_value('avg_rating', 0)       	
				try:
					rand_app.add_value('rating_count', app_context['userRatingCount'])
				except KeyError:
					self.logger.info('Index does not exist!')
					rand_app.add_value('rating_count', 0)
				try:
					rand_app.add_value('release_notes', app_context['releaseNotes'])
				except KeyError:
					self.logger.info('Index does not exist!')
					rand_app.add_value('release_notes', 0)       	  	 
				
				yield rand_app.load_item()

				# yield the app reviews page
				yield self._rev_page_request(app_id, APP_TYPE)

				#yield the app related page.
				yield Request(rand_app._values['app_store_url'], callback=self.parse_app_related_page, 
					meta= {'id': app_id, 'type': APP_TYPE, 'referrer': app_id})


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
				###########
				tmp_count = 0
				###########				
				for entry in feed.entries[1:]:		

						rand_review = SingleValItemLoader(item=RandReview(), response=response)
						rand_review.add_value('id', app_rvw_id_re.findall(entry['id'])[0])
						rand_review.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
						rand_review.add_value('title', entry['title'])
						rand_review.add_value('app_id', response.meta['id'])
						rand_review.add_value('comment', entry['content'][0]['value'])
						rand_review.add_value('reviewer_name', entry['author'])						
						rand_review.add_value('reviewer_id', app_rvwer_id_re.findall(entry['authors'][0]['href'])[0])
						rand_review.add_value('starRating', entry['im_rating'])
						rand_review.add_value('version', entry['im_version'])
						rand_review.add_value('vote', entry['im_votecount'])
						rand_review.add_value('country', 'us')
						rand_review.add_value('updated', datetime.datetime.fromtimestamp
							(int(calendar.timegm(entry['updated_parsed']))).strftime(settings['TS_FMT']))												
						# print(rand_review._values['updated'])						

						yield rand_review.load_item()

						# yield the reviewer						
						yield self._item_info_request(rand_review._values['reviewer_id'], RWR_TYPE, referrer=response.meta['id'])
						# yield self._item_info_request('286496943', RWR_TYPE, referrer=response.meta['id'])
						
						###########
						tmp_count += 1
						if tmp_count > 1:
							break
						###########
				# request subsequent pages to be downloaded
				# Find out the number of review pages
				noPages = int(app_page_re.findall(feed.feed['links'][3]['href'])[0])				
				# if response.meta['page'] < noPages:
				# 		yield self._successor_page_request(response)


		def parse_rvwer_profile_page(self, response):
				"""
				Parses review info by the reviewer in app store
				"""

				self.logger.info('Parsing review info by the same reviewer: %s  p%d' % (response.meta['id'], response.meta['page']))
				hxs = Selector(response)
				settings = self.crawler.settings

				rand_reviewer = SingleValItemLoader(item=RandReviewer(), response=response)
				rand_reviewer.add_value('id', response.meta['id'])
				rand_reviewer.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
				rand_reviewer.add_value('referrer', response.meta['referrer'])
				rvwer_page_title = only_elem_or_default(hxs.xpath('//body//div[@class="main-title"]/text()').extract())											
				startIdx = rvwer_page_title.find('by ')
				rvwer_name = rvwer_page_title[startIdx+3:]
				rand_reviewer.add_value('reviewer_name', rvwer_name)
				app_ids_reviewed = hxs.xpath('//body//a[@class="artwork-link"]/@href').re(app_id_re)
				rand_reviewer.add_value('nApps_rvwed', len(app_ids_reviewed))
				rand_reviewer.add_value('app_ids_rvwed', app_ids_reviewed)
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
				rand_reviewer.add_value('review_ratings', rev_ratings)
				rev_dates = hxs.xpath('//body//div[@class="review-date"]/text()').extract()
				rand_reviewer.add_value('review_dates', rev_dates)
				app_versions_reviewed = hxs.xpath('//body//button/@bundle-short-version').extract()
				rand_reviewer.add_value('app_versions_rvwed', app_versions_reviewed)
				app_developerIds_rvwed = hxs.xpath('//body//li[@class="artist"]/a/@href').re(app_id_re)
				rand_reviewer.add_value('app_devIds_rvwed', app_developerIds_rvwed)
				app_cats_rvwed = hxs.xpath('//body//li[@class="genre"]/text()').extract()
				try:
					rand_reviewer.add_value('app_cats_rvwed', app_cats_rvwed)						
				except KeyError:
					self.logger.info('Index does not exist!') 
					rand_reviewer.add_value('app_cats_rvwed', ' ')				
				app_releaseDates_str1_rvwed = hxs.xpath('//body//li[@class="release-date"]/span/text()').extract()
				app_releaseDates_str2_rvwed = hxs.xpath('//body//li[@class="release-date"]/text()').extract()
				app_releaseDates_str_rvwed = zip(app_releaseDates_str1_rvwed, app_releaseDates_str2_rvwed)
				app_releaseDates_rvwed = []
				for itm in app_releaseDates_str_rvwed:
					app_releaseDates_rvwed.append(''.join(itm))							
				rand_reviewer.add_value('app_releaseDates_rvwed', app_releaseDates_rvwed)
				app_review_titles = hxs.xpath('//body//div[@class="title-text"]/text()').extract()
				rand_reviewer.add_value('app_review_titles', app_review_titles)
				app_review_txts = hxs.xpath('//body//div[@class="review-block"]/p/text()').extract()
				rand_reviewer.add_value('app_review_txts', app_review_txts)				
				yield rand_reviewer.load_item()					
				
				# Find out current page and total number of review pages
				curPageNum = int(only_elem(hxs.xpath('//body//div[@class="paginated-content"]/@page-number').extract()))
				noPages = int(only_elem(hxs.xpath('//body//div[@class="paginated-content"]/@total-number-of-pages').extract()))
				if noPages == 1 and len(app_ids_reviewed) == 1:
					# assert only_elem(app_ids_reviewed) == response.meta['referrer']
					self.logger.info(r'Aborting unavailable reviewer page: %s' % response.url)
					return

				# for app_id in app_ids_reviewed:					
				# 	yield self._item_info_request(str(app_id), APP_TYPE, referrer=response.meta['id'])	

				if curPageNum == noPages:
					self.logger.info(r'Finishing crawling reviewer pages: %s' % response.url)
					return
				# request subsequent review pages to be downloaded				
				# if response.meta['page'] < noPages:
				# 		yield self._successor_page_request(response)			


		def parse_app_related_page(self, response):
				"""
				Parses apps from an app related page in app store
				"""

				self.logger.info('Parsing apps related to: %s' % response.meta['id'])
				hxs = Selector(response)
				rand_apps_related = SingleValItemLoader(item=RandRelatedApps(), response=response)
				rand_apps_related.add_value('id', response.meta['referrer'])

				apps_ids_bought = hxs.xpath('//body//div[contains(h2/text(), "Customers Also Bought")]/following-sibling::div[@num-items="10"]//a[@class="artwork-link"]/@href').re(app_id_re)				

				rand_apps_related.add_value('nApps_related', len(apps_ids_bought))				
				rand_apps_related.add_value('app_ids_related', apps_ids_bought)
				yield rand_apps_related.load_item()				
				
				# if apps_ids_bought: 
				# 	for app_id in apps_ids_bought:											
						# yield self._item_info_request(str(app_id), APP_TYPE, referrer=response.meta['referrer'])
				
				dev_id = hxs.xpath('//body//h4[contains(text(), "More by")]/a/@href').re(dev_id_re)
				if dev_id:	
					# yield self._item_info_request(only_elem(dev_id), DEV_TYPE, referrer=response.meta['referrer'])
					yield self._item_info_request(only_elem(dev_id), DEV_IPHONE_TYPE, referrer=response.meta['referrer'])
					yield self._item_info_request(only_elem(dev_id), DEV_IPAD_TYPE, referrer=response.meta['referrer'])
				

		def parse_dev_profile_page(self, response):
				"""
					Parses apps from same developer in app store
				"""
				self.logger.info('Parsing apps by the same developer: %s  %s Apps' % (response.meta['id'], response.meta['type']))
				settings = self.crawler.settings  
				hxs = Selector(response)

				rand_developer = SingleValItemLoader(item=RandDeveloper(), response=response)
				dev_name_title = only_elem_or_default(hxs.xpath('//body//h1//text()').extract())
				startIdx = dev_name_title.find('By ')
				name = dev_name_title[startIdx+3:]
				rand_developer.add_value('name', name)
				rand_developer.add_value('id', response.meta['id'])
				rand_developer.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
				rand_developer.add_value('referrer', response.meta['referrer'])
				app_ids = hxs.xpath('//body//a[@class="artwork-link"]/@href').re(app_id_re)				
				if app_ids:
					rand_developer.add_value('app_type_deved', response.meta['type'].decode('utf-8', 'ignore'))
					rand_developer.add_value('nApps_deved', len(app_ids))				
					rand_developer.add_value('app_ids_deved', app_ids)
					yield rand_developer.load_item()

					if len(app_ids) == 1:
						assert only_elem(app_ids) == response.meta['referrer']
						self.logger.info(r'Aborting unavailable developer page: %s' % response.url)
						return

					# for app_id in app_ids:
					# 	yield self._item_info_request(str(app_id), APP_TYPE, referrer=response.meta['id'])	
				else:
					yield rand_developer.load_item()
