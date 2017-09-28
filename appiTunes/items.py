# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field
from scrapy.loader.processors import Compose, MapCompose
from appiTunes.utils import only_elem, only_elem_or_default, filter_empty

__author__ = 'Shanshan'

class App(Item):
	# define the fields for your item here like:
	id = Field()
	timestamp = Field()
	label = Field()
	app_name = Field()
	countries = Field()
	enabled = Field(input_processor=Compose(int))
	iphone = Field(input_processor=Compose(int))
	ipad = Field(input_processor=Compose(int))
	osx = Field(input_processor=Compose(int))
	description = Field(input_processor=Compose(MapCompose(unicode.strip), filter_empty))
	image_url = Field()
	app_store_url = Field()	
	bundleId = Field()
	developer_id = Field()
	developer_name = Field()
	release_date = Field()
	price = Field(input_processor=Compose(float))
	genres = Field(input_processor=MapCompose(unicode.strip))
	main_cat = Field()
	rating_count_for_cur_version = Field(input_processor=Compose(int))
	content_rating_age_group = Field(input_processor=Compose(unicode.strip))
	avg_rating_for_cur_version = Field(input_processor=Compose(float))
	languages = Field(input_processor=MapCompose(unicode.strip))
	cur_ver_release_date = Field()
	app_type = Field()
	version = Field()
	currency = Field()
	release_notes = Field()
	avg_rating = Field(input_processor=Compose(float))
	rating_count = Field(input_processor=Compose(int))
	min_os_version = Field()
	referrer = Field()

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'app'


class RelatedApps(Item):
	id = Field()	
	nApps_related = Field(input_processor=Compose(int))
	app_ids_related = Field(input_processor=MapCompose(unicode.strip))	

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'apps_related'


class Review(Item):
	id = Field()
	timestamp = Field()
	app_id = Field()
	version = Field()
	reviewer_id = Field()
	reviewer_name = Field()
	updated = Field()
	title = Field()
	starRating = Field(input_processor=Compose(only_elem, int))
	vote = Field(input_processor=MapCompose(int))
	comment = Field(input_processor=Compose(MapCompose(unicode.strip), filter_empty, lambda vs: ' '.join(vs)))
	country = Field()

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'review'


class Developer(Item):
	id = Field()
	timestamp = Field()
	name = Field()
	nApps_deved = Field(input_processor=Compose(int))
	# app_type_deved = Field(input_processor=MapCompose(unicode.strip))
	app_ids_deved = Field(input_processor=MapCompose(unicode.strip))
	referrer = Field()

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'developer'


class Reviewer(Item):
	id = Field()
	timestamp = Field()
	reviewer_name = Field()
	nApps_rvwed = Field(input_processor=Compose(int))	
	app_ids_rvwed = Field(input_processor=MapCompose(unicode.strip))
	app_cats_rvwed = Field(input_processor=MapCompose(unicode.strip))
	review_ratings = Field(input_processor=MapCompose(unicode.strip))
	review_dates = Field(input_processor=MapCompose(unicode.strip))
	app_versions_rvwed = Field(input_processor=MapCompose(unicode.strip))
	app_devIds_rvwed = Field(input_processor=MapCompose(unicode.strip))
	app_releaseDates_rvwed = Field(input_processor=MapCompose(unicode.strip))
	app_review_titles = Field(input_processor=MapCompose(unicode.strip))
	app_review_txts = Field(input_processor=MapCompose(unicode.strip))
	referrer = Field()

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'reviewer'


class RandApp(Item):
	# define the fields for your item here like:
	id = Field()
	label = Field()
	app_name = Field()
	countries = Field()
	enabled = Field(input_processor=Compose(int))
	iphone = Field(input_processor=Compose(int))
	ipad = Field(input_processor=Compose(int))
	osx = Field(input_processor=Compose(int))
	description = Field(input_processor=Compose(MapCompose(unicode.strip), filter_empty))
	image_url = Field()
	app_store_url = Field()
	timestamp = Field()
	bundleId = Field()
	developer_id = Field()
	developer_name = Field()
	release_date = Field()
	price = Field(input_processor=Compose(float))
	genres = Field(input_processor=MapCompose(unicode.strip))
	main_cat = Field()
	rating_count_for_cur_version = Field(input_processor=Compose(int))
	content_rating_age_group = Field(input_processor=Compose(unicode.strip))
	avg_rating_for_cur_version = Field(input_processor=Compose(float))
	languages = Field(input_processor=MapCompose(unicode.strip))
	cur_ver_release_date = Field()
	app_type = Field()
	version = Field()
	currency = Field()
	# release_notes = Field(input_processor=Compose(MapCompose(unicode.strip), filter_empty))
	release_notes = Field()
	avg_rating = Field(input_processor=Compose(float))
	rating_count = Field(input_processor=Compose(int))
	min_os_version = Field()
	# rank = Field(input_processor=Compose(int))
	# rank_list_name = Field()
	referrer = Field()

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'rand_app'


class RandRelatedApps(Item):
	id = Field()	
	nApps_related = Field(input_processor=Compose(int))
	app_ids_related = Field(input_processor=MapCompose(unicode.strip))	

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'rand_apps_related'


class RandReview(Item):
	id = Field()
	timestamp = Field()
	app_id = Field()
	version = Field()
	reviewer_id = Field()
	reviewer_name = Field()
	updated = Field()
	title = Field()
	starRating = Field(input_processor=Compose(only_elem, int))
	vote = Field(input_processor=MapCompose(int))
	comment = Field(input_processor=Compose(MapCompose(unicode.strip), filter_empty, lambda vs: ' '.join(vs)))
	country = Field()

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'rand_review'


class RandDeveloper(Item):
	id = Field()
	timestamp = Field()
	name = Field()
	nApps_deved = Field(input_processor=Compose(int))
	app_type_deved = Field(input_processor=MapCompose(unicode.strip))
	app_ids_deved = Field(input_processor=MapCompose(unicode.strip))
	referrer = Field()

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'rand_developer'


class RandReviewer(Item):
	id = Field()
	timestamp = Field()
	reviewer_name = Field()
	nApps_rvwed = Field(input_processor=Compose(int))	
	app_ids_rvwed = Field(input_processor=MapCompose(unicode.strip))
	app_cats_rvwed = Field(input_processor=MapCompose(unicode.strip))
	review_ratings = Field(input_processor=MapCompose(unicode.strip))
	review_dates = Field(input_processor=MapCompose(unicode.strip))
	app_versions_rvwed = Field(input_processor=MapCompose(unicode.strip))
	app_devIds_rvwed = Field(input_processor=MapCompose(unicode.strip))
	app_releaseDates_rvwed = Field(input_processor=MapCompose(unicode.strip))
	app_review_titles = Field(input_processor=MapCompose(unicode.strip))
	app_review_txts = Field(input_processor=MapCompose(unicode.strip))
	referrer = Field()

	@property
	def key(self):
		return self._values['id']

	@property
	def export_filename(self):
		return 'rand_reviewer'
