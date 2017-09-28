# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.conf import settings 
import pymongo

import scrapy
import logging

class AppleMongoDBPipeline(object):
	def __init__(self):
		connectionAPP = pymongo.MongoClient(
			settings['MONGODB_SERVER'],
			settings['MONGODB_PORT']
			)
		connectionREV = pymongo.MongoClient(
			settings['MONGODB_SERVER'],
			settings['MONGODB_PORT']
			)
		connectionDEV = pymongo.MongoClient(
			settings['MONGODB_SERVER'],
			settings['MONGODB_PORT']
			)
		connectionRWR = pymongo.MongoClient(
			settings['MONGODB_SERVER'],
			settings['MONGODB_PORT']
			)
		
		db_app = connectionAPP[settings['MONGODB_ITUNES_APP_DB']]
		db_rev = connectionREV[settings['MONGODB_ITUNES_APP_DB']]
		db_dev = connectionDEV[settings['MONGODB_ITUNES_APP_DB']]
		db_rwr = connectionRWR[settings['MONGODB_ITUNES_APP_DB']]
		
		self.connectionAPP = db_app[settings['MONGODB_APP_COLLECTION']]
		self.connectionREV = db_rev[settings['MONGODB_REVIEW_COLLECTION']]
		self.connectionDEV = db_dev[settings['MONGODB_DEV_COLLECTION']]
		self.connectionRWR = db_rwr[settings['MONGODB_RWR_COLLECTION']]

		# random app database connection
		connectionRandAPP = pymongo.MongoClient(
			settings['MONGODB_SERVER'],
			settings['MONGODB_PORT']
			)
		connectionRandREV = pymongo.MongoClient(
			settings['MONGODB_SERVER'],
			settings['MONGODB_PORT']
			)
		connectionRandDEV = pymongo.MongoClient(
			settings['MONGODB_SERVER'],
			settings['MONGODB_PORT']
			)
		connectionRandRWR = pymongo.MongoClient(
			settings['MONGODB_SERVER'],
			settings['MONGODB_PORT']
			)
		
		db_rand_app = connectionRandAPP[settings['MONGODB_ITUNES_RAND_APP_DB']]
		db_rand_rev = connectionRandREV[settings['MONGODB_ITUNES_RAND_APP_DB']]
		db_rand_dev = connectionRandDEV[settings['MONGODB_ITUNES_RAND_APP_DB']]
		db_rand_rwr = connectionRandRWR[settings['MONGODB_ITUNES_RAND_APP_DB']]
		
		self.connectionRandAPP = db_rand_app[settings['MONGODB_RAND_APP_COLLECTION']]
		self.connectionRandREV = db_rand_rev[settings['MONGODB_RAND_REVIEW_COLLECTION']]
		self.connectionRandDEV = db_rand_dev[settings['MONGODB_RAND_DEV_COLLECTION']]
		self.connectionRandRWR = db_rand_rwr[settings['MONGODB_RAND_RWR_COLLECTION']]

	def process_item(self, item, spider):	
		connection = pymongo.MongoClient('localhost',27017)
		db_app = connection[settings['MONGODB_ITUNES_APP_DB']]
		db_rand_app = connection[settings['MONGODB_ITUNES_RAND_APP_DB']]

		if item.export_filename == 'app':
			self.connectionAPP.update({'id': item['id']}, dict(item), upsert=True)

		if item.export_filename == 'apps_related':
			self.connectionAPP.update({'id': item['id']}, dict(item), upsert=True)
			# res = db_app['apps'].find_one({'id':item['id']})			
			# if res:
			# 	if item['nApps_related'] != 0:				
			# 		self.connectionAPP.update({'id': res['id']}, {'$set' : {'nApps_related':item['nApps_related'], 'app_ids_related':item['app_ids_related']}})				

		if item.export_filename == 'review':
			self.connectionREV.update({'id': item['id']}, dict(item), upsert=True)    

		if item.export_filename == 'developer':
			self.connectionDEV.update({'id': item['id']}, dict(item), upsert=True)
			# res = db_app['developers'].find_one({'id':item['id']})			
			# if res:
			# 	if len(item) == 7:
			# 		try:					
			# 			res['app_ids_deved'] = list(set(res['app_ids'] + item['app_ids']))
			# 			res['nApps_deved'] = len(res['app_ids_deved'])
			# 			# res['app_type_deved'] = list(set(res['app_ids_deved'] + item['app_ids_deved']))
			# 			res['timestamp'] = item['timestamp']
			# 			self.connectionDEV.update({'id': res['id']}, dict(res), upsert=True)
			# 		except KeyError:					
			# 			self.connectionDEV.update({'id': res['id']}, {'$set' : {'app_ids_deved':item['app_ids_deved'], 'nApps_deved':item['nApps_deved']}})
			# else:
			# 	self.connectionDEV.insert(dict(item))		

		if item.export_filename == 'reviewer':
			res = db_app['reviewers'].find_one({'id':item['id']})			
			if res:
				res['timestamp'] = item['timestamp']
				res['nApps_rvwed'] += item['nApps_rvwed']
				res['app_ids_rvwed'] += item['app_ids_rvwed']
				res['app_cats_rvwed'] += item['app_cats_rvwed']
				res['review_ratings'] += item['review_ratings']
				res['review_dates'] += item['review_dates']
				res['app_versions_rvwed'] += item['app_versions_rvwed']
				res['app_devIds_rvwed'] += item['app_devIds_rvwed']
				res['app_releaseDates_rvwed'] += item['app_releaseDates_rvwed']
				res['app_review_titles'] += item['app_review_titles']
				res['app_review_txts'] += item['app_review_txts']				
				self.connectionRWR.update({'id': res['id']}, dict(res), upsert=True)
			else:
				self.connectionRWR.insert(dict(item))		

		# random app stored in database
		if item.export_filename == 'rand_app':
			self.connectionRandAPP.update({'id': item['id']}, dict(item), upsert=True)

		if item.export_filename == 'rand_apps_related':
			res = db_app['apps'].find_one({'id':item['id']})			
			if res:
				self.connectionRandAPP.update({'id': res['id']}, {'$set' : {'nApps_related':item['nApps_related'], 'app_ids_related':item['app_ids_related']}})	

		if item.export_filename == 'rand_review':
			self.connectionRandREV.update({'id': item['id']}, dict(item), upsert=True)    

		if item.export_filename == 'rand_developer':			
			res = db_rand_app['developers'].find_one({'id':item['id']})
			if res:
				if len(item) == 7:
					try:					
						res['app_ids_deved'] = list(set(res['app_ids'] + item['app_ids']))
						res['nApps_deved'] = len(res['app_ids_deved'])
						# res['app_type_deved'] = list(set(res['app_ids_deved'] + item['app_ids_deved']))
						res['timestamp'] = item['timestamp']
						self.connectionRandDEV.update({'id': res['id']}, dict(res), upsert=True)
					except KeyError:					
						self.connectionRandDEV.update({'id': res['id']}, {'$set' : {'app_ids_deved':item['app_ids_deved'], 'nApps_deved':item['nApps_deved']}})
			else:
				self.connectionRandDEV.insert(dict(item))

		if item.export_filename == 'rand_reviewer':
			res = db_rand_app['reviewers'].find_one({'id':item['id']})			
			if res:
				res['timestamp'] = item['timestamp']
				res['nApps_rvwed'] += item['nApps_rvwed']
				res['app_ids_rvwed'] += item['app_ids_rvwed']
				res['app_cats_rvwed'] += item['app_cats_rvwed']
				res['review_ratings'] += item['review_ratings']
				res['review_dates'] += item['review_dates']
				res['app_versions_rvwed'] += item['app_versions_rvwed']
				res['app_devIds_rvwed'] += item['app_devIds_rvwed']
				res['app_releaseDates_rvwed'] += item['app_releaseDates_rvwed']
				res['app_review_titles'] += item['app_review_titles']
				res['app_review_txts'] += item['app_review_txts']				
				self.connectionRandRWR.update({'id': res['id']}, dict(res), upsert=True)
			else:
				self.connectionRandRWR.insert(dict(item))

		return item
