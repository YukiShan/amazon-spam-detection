"""
This modules implements a crawler to scrape Amazon web site based on a seed list of
products and member pages.

"""
__author__ = 'Shanshan'

import datetime
import csv
from scrapy.selector import Selector
from scrapy.utils.misc import arg_to_iter
from scraper.items import Member, Product, Review
import scrapy
import logging
from scrapy.http import Request
from scrapy.spiders import Spider
from scraper.utils import SingleValItemLoader, only_elem_or_default, MEMBER_TYPE, PROD_TYPE
from lxml import etree
from urlparse import urljoin
import pymongo

review_id_re = r'(?:(?:/review/))(\w+)'
number_digit_grpd = r'\d+(?:,\d+)*'
cat_name_re = r'\w+(?:\s+(?:\w+|\&))*'
sales_rank_re = r'#(%s)\s+(?:\w+\s+)?in\s+(%s)' % (number_digit_grpd, cat_name_re)
price_re = r'\$(%s\.\d\d)' % number_digit_grpd
star_rating_re = r'(\d+(?:\.\d+)?)\s+out\s+of'
product_url_id_re = r'(?:(?:/gp/product/)|(?:/gp/product/glance/)|(?:/dp/))(\w+)'
member_url_id_re = r'(?<=profile/)\w+'


def xpath_lower_case(context, a):
    return [s.lower() for s in a]


ns = etree.FunctionNamespace(None)
ns['lower-case'] = xpath_lower_case


def _member_profile_url(m_id):
    s = 'https://www.amazon.com/gp/pdp/profile/%s/' % m_id
    # print(">>>>>>>>>>test")
    # print(s)
    return s

def _member_rev_url(m_id, page=1):
    s = 'https://www.amazon.com/gp/cdp/member-reviews/%s/?page=%d&sort_by=MostRecentReview' % (m_id, page)
    return s

def _product_details_url(p_id):
    s = 'https://www.amazon.com/dp/%s/' % p_id
    return s

def _product_rev_url(p_id, page=1):
    # s = 'http://www.amazon.com/product-reviews/%s?showViewpoints=1&sortBy=recent&pageNumber=%d' % (p_id, page)
    s = 'https://www.amazon.com/product-reviews/%s?showViewpoints=1&sortBy=helpful&pageNumber=%d' % (p_id, page)
    return s


class AmazonSpider(Spider):
    """
    A spider to crawl Amazon product and member pages
    """

    name = "scraper"
    allowed_domains = ["amazon.com"]

    def __init__(self, **kwargs):
        super(AmazonSpider, self).__init__(**kwargs)
        self.rev_req_param = {
                              MEMBER_TYPE: (_member_rev_url, self.parse_member_rev_page), 
                              PROD_TYPE: (_product_rev_url, self.parse_product_rev_page)}
        self.item_req_param = {
                               MEMBER_TYPE: (_member_profile_url, self.parse_member_profile_page),
                               PROD_TYPE: (_product_details_url, self.parse_product_details_page)}

    def _item_page_request(self, id_, type_, referrer):
        item_url_gen, cb = self.item_req_param[type_]
        req_meta = {'id': id_, 'type': type_, 'referrer': referrer}
        # print (">>>>>>  _item_page_request  <<<<<<<")
        # print ("type ", type_)
        # print("test _item_page_request()")
        return Request(item_url_gen(id_), callback=cb, meta=req_meta)

    def _rev_page_request(self, id_, type_, p=1):
        rev_url_gen, cb = self.rev_req_param[type_]
        req_meta = {'id': id_, 'type': type_, 'page': p}
        return Request(rev_url_gen(id_, p), callback=cb, meta=req_meta)

    def _successor_page_request(self, response):
        type_, id_ = response.meta['type'], response.meta['id']
        next_p = response.meta['page'] + 1
        return self._rev_page_request(id_, type_, next_p)

    def parse_member_profile_page(self, response):
        """
        Parses member profile page
        """

        self.logger.info('Parsing member info: %s' % response.meta['id'])
        # from scrapy.shell import inspect_response
        # inspect_response(response)
        member_id = response.meta['id']
        settings = self.crawler.settings
        hxs = Selector(response)
        contentTest = response.body
        # print (">>>>>>>test here 100000000000 <<<<<<<<<<<")
        # print(response.url)

        # Abort if member reviews are not available
        if hxs.xpath('//body//b[@class="h1" and contains(text(), "this customer\'s list of reviews is currently not available")]'):
            self.logger.info(r'Aborting unavailable member page: %s' % response.url)
            return

        # yield the reviewer info
        # print (">>>>>>>id ", member_id,"<<<<<<<<<<<")
        member = SingleValItemLoader(item=Member(), response=response)
        member.add_value('id', member_id)
        # if no fullname crawled, then try request it again to ensure that proxy really returned the target page
        # if not hxs.xpath('//body//span[@class="public-name-text"]/text()').extract():
        #     print (">>>>>>>>>>999999999999999<<<<<<<<<<")
        #     # print (member._values['id'])
        #     yield Request(url=response.url, dont_filter=True)

        print (">>>>>>>test here 101 <<<<<<<<<<<")
        testName = hxs.xpath('//body//span[@class="public-name-text"]/text()').extract()
        print(testName)
        member.add_value('fullname', hxs.xpath('//body//span[@class="public-name-text"]/text()').extract())
        member.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
        # print (">>>>>>>test here 222222222 <<<<<<<<<<<")
        # print (member._values['fullname'])
        # member.add_value('badges', hxs.xpath('//body//div[@id="profileHeader"]//div[@class="badges"]//a/img/@alt').re(r'\((.+)\)'))
        # For top reviewers the ranking is inside an anchor while for lower rank people it's part of a text()
        ranking = hxs.xpath('//body//div[contains(span/text(),"Reviewer ranking")]//div//span/text()')   .re(r'\d+(?:,\d+)*') or \
                  hxs.xpath('//body//div[contains(a/span/text(),"Reviewer ranking")]//div//span//text()').re(r'\d+(?:,\d+)*')
        # ranking = ranking or hxs.xpath('//body//div[@id="reviewsStripe"]/div[@class="stripeContent"]/div//text()').re(r'Top Reviewer Ranking:\s+(%s)' % number_digit_grpd)
        # 
        # print(len(ranking))
        # print(ranking)

        member.add_value('ranking', ranking)
        member.add_value('helpfulStat', hxs.xpath('//body//div[contains(span/text(),"Helpful votes")]//following-sibling::div[@class="value"]//span/text()').re(r'\d+'))
        member.add_value('location', hxs.xpath('(//body//div[contains(@class, "location-and-occupation-holder")]//div//span)[position()=last()]/text()').extract())
        
        # global review_stat
        # no_of_reviews_url = hxs.xpath('//body//div[contains(@data-story-id, "Glimpse:REVIEW")][1]//a[@class="a-link-normal" and contains(@href,"review")]/@href')
        # print (">>>>>>>test here 22222222222222 <<<<<<<<<<<")
        # print(hxs.xpath('//body//div[contains(@data-story-id, "Glimpse:REVIEW")]')) 
        # yield Request(no_of_reviews_url, callback=self.parse_no_reviews_url)
        # member.add_value('reviewStat', review_stat)

        # no_reviews = len(hxs.xpath('//body//div[contains(@data-story-id, "Glimpse:REVIEW")]//div[contains(@class, "glimpse-product-content")]//img[@class= "glimpse-product-image"]'))
        # print (">>>>>>>test here 116 <<<<<<<<<<<")
        # print(no_reviews)
        # for large number of reviews, there are only 20 reviews in one page. No information showing its real large num.So we only count the low number of reviews
        # if no_reviews < 20:
        #     review_stat = no_reviews
        # member._add_value('reviewStat', review_stat)        
        # _item = member.load_item()
        # print(item)
        # yield _item        
        yield member.load_item()
        # yield the reviews written by the member
        yield self._rev_page_request(member_id, MEMBER_TYPE)

        # member.add_value('reviewStat', review_stat)
        # print (">>>>>>>test here 120 <<<<<<<<<<<")
        # print(member._values['reviewStat'])
        

    # def parse_no_reviews_url(self, response):
    #     """
    #     Parses a specific member reviews page to get the member's review number
    #     """
    #     hxs = Selector(response)
    #     review_stat = hxs.xpath('//div[contains(@id, "ReviewerInfo")]/div[contains(@class, "AuthorInfo")]//a[contains(@href,"reviews")]/text()').re(number_digit_grpd)


    def parse_member_rev_page(self, response):
        """
        Parses a member reviews page and makes requests for subsequent pages
        """

        self.logger.info('Parsing member reviews: %s p%d' % (response.meta['id'], response.meta['page']))

        hxs = Selector(response)
        member_id = response.meta['id']
        settings = self.crawler.settings
        print(">>>>>>>test here 130 <<<<<<<<<<<")
        print(response.url)
        # yield each review
        
        # if no significant element crawled, then try request it again to ensure that proxy really returned the target page
        # if not hxs.xpath('//tbody/tr//b[@class="h1"]/text()[1]').extract():
        #     yield Request(url=response.url, dont_filter=True)
        # review_stat = hxs.xpath('//td[@valign="top"]/table//div[@class="small"]/text()').re(r'(?:(\d+))')
        rev_body_elems = hxs.xpath('//table//td[not(@width)]//table//tr[not(@valign)]/td[@class="small"]/div')
        rev_header_elems = hxs.xpath('//table//td[not(@width)]//table//tr[@valign]/td[@align][2]//table[@class="small"]')
        for rev_header, rev_body in zip(rev_header_elems, rev_body_elems):
            # populating review data
            review = SingleValItemLoader(item=Review(), response=response)
            # print(">>>>>>>test here 140 <<<<<<<<<<<")
            product_id = only_elem_or_default(rev_header.xpath('.//b/a/@href').re(product_url_id_re))
            if product_id:
                product_id = str(product_id)
                # print(">>>>>>>test here 150 <<<<<<<<<<<")
                # print(product_id)
            star_rating_tmp = rev_body.xpath('.//span/img[contains(@title, "stars")]/@title').re(star_rating_re)
            # print(">>>>>>>test here 150 <<<<<<<<<<<")
            # print(star_rating_tmp)
            if not star_rating_tmp:
                # The review is probably a manufacturer response and not an actual review
                continue
            review.add_value('starRating', star_rating_tmp)
            review.add_value('productId', product_id)
            # print(">>>>>>>test here 160 <<<<<<<<<<<")
            # print(review._values['productId'])
            review.add_value('memberId', member_id)
            # print(">>>>>>>test here 170 <<<<<<<<<<<")
            # print(review._values['memberId'])
            review.add_value('id', rev_body.xpath('.//a[contains(text(), "Permalink")]/@href').re(review_id_re))
            # print(">>>>>>>test here 180 <<<<<<<<<<<")
            # print(review._values['id'])            
            review.add_value('helpful', rev_body.xpath('./div[contains(text(), "helpful")]/text()').re(r'\d+'))
            review.add_value('title', rev_body.xpath('div/span[contains(img/@alt, "stars")]/following-sibling::b[1]/text()').extract())
            review.add_value('date', rev_body.xpath('div/nobr/text()').extract())          
            review.add_value('verifiedPurchase', rev_body.xpath('.//span[contains(@class, "crVerifiedStripe")]'))            
            review.add_value('reviewTxt', rev_body.xpath('./div[@class="reviewText"]/text()').extract())            
            nComments_tmp = only_elem_or_default(rev_body.xpath('.//div/a/text()').re(r'Comments?\s+\((\d+)\)'), '0')
            review.add_value('nComments', nComments_tmp)
            # print(">>>>>>>test here 180 <<<<<<<<<<<")
            # print(review._values['nComments'])
            review.add_value('vine', rev_body.xpath('.//span/b[contains(text(), "Customer review from the Amazon Vine Program")]'))
            review.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
            yield review.load_item()

            # yield the product
            yield self._item_page_request(product_id, PROD_TYPE, referrer=member_id)

        #make request for subsequent pages
        if hxs.xpath('//table//table//td[@class="small"]/b/text()').re(r'(\d+)\s+\|'):
            # s = hxs.xpath('//table//table//td[@class="small"]/b/text()').re(r'(\d+)\s+\|')
            # print(">>>>>>>test here 8888888888888888888 <<<<<<<<<<<")
            # print(s)
            yield self._successor_page_request(response)


    def parse_product_details_page(self, response):
        """
        Extracts information from a product page and yields its review page and pages of products in the same category
        """
        self.logger.info('Parsing product info: %s' % response.meta['id'])
        # from scrapy.shell import inspect_response
        # inspect_response(response)
        settings = self.crawler.settings
        hxs = Selector(response)
        product_id = response.meta['id']

        
        # yield product details
        name = hxs.xpath('//body//span[@id="productTitle"]/text()').extract() or \
               hxs.xpath('//body//div[@id="title_feature_div"]//h1//span/text()').extract()
        if not name:
            name = hxs.xpath('//head/title/text()').re(r'(?:Amazon:\s+)?([^:]+)')
            # name = _getName(hxs)
        
        # if no significant element crawled, then try request it again to ensure that proxy really returned the target page
        # if (not name) or (name =="Robot Check"):
        #     yield Request(url=response.url, dont_filter=True)

        price = hxs.xpath('//body//span[@id="priceblock_ourprice" or @id="priceblock_saleprice"]//text()').re(price_re) or \
                hxs.xpath('//body//div[@id="price"]//span[contains(@class, "a-color-price")]/text()').re(price_re) or \
                hxs.xpath('//body//div[@id="price_feature_div"]//span[@class="a-size-medium a-color-price"]/text()').re(price_re)
        manufact_node1 = hxs.xpath('//body//span[@class="brandFrom"]/following-sibling::a[@id="brand"]')
        manufact_node2 = hxs.xpath('(//body//div[@id="brandByline_feature_div"]//a[@id="brand"])[1]') or \
                        hxs.xpath('//body//div[@id="byline"]/span[1]//a[contains(@class,"contributorNameID")]')
        if manufact_node1:
            manufact_node = manufact_node1
            manufact_flag= 1
            manufact = manufact_node.xpath('./text()').extract()
            manufact_href = manufact_node.xpath('./@href').extract()
        else:
            if manufact_node2:
               manufact_node = manufact_node2
               manufact_flag= 2
               manufact = manufact_node.xpath('./text()').extract()
               manufact_href = manufact_node.xpath('./@href').extract()
            else:
               manufact_flag, manufact, manufact_href = None, [], []
        avg_stars, n_reviews = None, None
        reviews_t = hxs.xpath('//body//div[@id="leftCol" or @id="centerCol" ]//div[@id="averageCustomerReviews"]')
        if reviews_t:
            avg_stars = reviews_t.xpath('.//span[contains(@title, "star")]/@title').re(star_rating_re)
            n_reviews = reviews_t.xpath('.//a[contains(@href, "customerReviews")]/span/text()').re(number_digit_grpd)
        else:
            #need to check review_t
            reviews_t = hxs.xpath('(//body//*[self::div[@class="buying"] or self::form[@id="handleBuy"]]//span[@class="crAvgStars"])[1]')
            if reviews_t:
                avg_stars = reviews_t.xpath('.//span[contains(@title, "star")]/@title').re(star_rating_re)
                n_reviews = reviews_t.xpath('.//span[@id="acrCustomerReviewText"]/text()').re(number_digit_grpd)

        sales_rank, cat, sub_cat_rank, sub_cat = [None]*4
        best_sellers_href, sub_cat_href = [], []
        parent_node = hxs.xpath('//body//li[@id="SalesRank"]')
        if parent_node:
            sales_rank, cat = parent_node.xpath('./text()').re(sales_rank_re) or [None]*2
            best_sellers_href = parent_node.xpath('./a[contains(lower-case(text()), "see top") and (contains(@href, "/best-sellers") or contains(@href, "/bestsellers"))]/@href').extract()
            # best_sellers_txt = parent_node.xpath('./a[contains(lower-case(text()), "see top") and (contains(@href, "/best-sellers") or contains(@href, "/bestsellers"))]/text()').extract()
            
            sub_cat_node = parent_node.xpath('.//li[@class="zg_hrsr_item"][1]')
            if sub_cat_node:
                sub_cat_rank = sub_cat_node.xpath('./span[@class="zg_hrsr_rank"]/text()').re(number_digit_grpd)
                sub_cat = sub_cat_node.xpath('(./span[@class="zg_hrsr_ladder"]//a)[position()=last()]/text()').extract()
                sub_cat_href = sub_cat_node.xpath('(./span[@class="zg_hrsr_ladder"]//a)[position()=last()]/@href').extract()
                
        if not parent_node:
            # parent_node = hxs.xpath('//body//div[@id="detailBullets"]//span[contains(b/text(), "Amazon Best Sellers Rank")]')
            parent_node = hxs.xpath('//body//div[@id="prodDetails"]//tr[contains(th/text(),"Best Sellers Rank")]')
            if parent_node:
                sales_rank, cat = parent_node.xpath('.//span[1]/text()').re(sales_rank_re) or [None]*2
                best_sellers_href = parent_node.xpath('.//span[1]/a[contains(lower-case(text()), "see top") and (contains(@href, "/best-sellers") or contains(@href, "/bestsellers"))]/@href').extract()
                # sub_cat_node = parent_node.xpath('.//span[2]')
                # if sub_cat_node:
                # best_sellers_txt = parent_node.xpath('.//span[1]/a[contains(lower-case(text()), "see top") and (contains(@href, "/best-sellers") or contains(@href, "/bestsellers"))]/text()').extract()
                # print(">>>>>>>test here 33333 <<<<<<<<<<<")
                # print(best_sellers_txt)
                sub_cat_rank = parent_node.xpath('.//span[2]/text()').re(number_digit_grpd)
                sub_cat = parent_node.xpath('(.//span[2]//a)[position()=last()]/text()').extract()
                sub_cat_href = parent_node.xpath('(.//span[2]//a)[position()=last()]/@href').extract()
        if not parent_node:
            parent_node = hxs.xpath('//body//tr[@id="SalesRank"]')
            if parent_node:
                sales_rank, cat = parent_node.xpath('./text()').re(sales_rank_re) or [None]*2
                best_sellers_href = parent_node.xpath('./a[contains(lower-case(text()), "see top") and (contains(@href, "/best-sellers") or contains(@href, "/bestsellers"))]/@href').extract()
                sub_cat_node = parent_node.xpath('.//li[@class="zg_hrsr_item"][1]')
                if sub_cat_node:
                    sub_cat_rank = sub_cat_node.xpath('./span[@class="zg_hrsr_rank"]/text()').re(number_digit_grpd)
                    sub_cat = sub_cat_node.xpath('(./span[@class="zg_hrsr_ladder"]//a)[position()=last()]/text()').extract()
                    sub_cat_href = sub_cat_node.xpath('(./span[@class="zg_hrsr_ladder"]//a)[position()=last()]/@href').extract()

        product = SingleValItemLoader(item=Product(), response=response)
        product.add_value('id', product_id)
        product.add_value('name', name)
        # print(">>>>>>>test here 200 <<<<<<<<<<<")
        # print(product._values['id'])
        product.add_value('price', price)
        # print(">>>>>>>test here 210 <<<<<<<<<<<")
        # print(product._values['price'])
        product.add_value('avgStars', avg_stars)
        # print(">>>>>>>test here 220 <<<<<<<<<<<")
        # print(product._values['avgStars'])
        product.add_value('nReviews', n_reviews)
        # print(">>>>>>>test here 230 <<<<<<<<<<<")
        # print(product._values['nReviews'])
        product.add_value('salesRank', sales_rank)
        # print(">>>>>>>test here 240 <<<<<<<<<<<")
        # print(product._values['salesRank'])
        product.add_value('cat', cat)
        # print(">>>>>>>test here 250 <<<<<<<<<<<")
        # print(product._values['cat'])
        product.add_value('subCatRank', sub_cat_rank)
        # print(">>>>>>>test here 260 <<<<<<<<<<<")
        # print(product._values['subCatRank'])
        product.add_value('subCat', sub_cat)
        # print(">>>>>>>test here 270 <<<<<<<<<<<")
        # print(product._values['subCat'])
        product.add_value('manufact', manufact)
        # print(">>>>>>>test here 280 <<<<<<<<<<<")
        # print(product._values['manufact'])
        product.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
        yield product.load_item()

        # yield same category and same manufacturer products
        same_cat_href = only_elem_or_default(sub_cat_href or best_sellers_href)
        # print(">>>>>>>test here 22222 <<<<<<<<<<<")
        # print(best_sellers_href)
        # print(">>>>>>>test here 33333 <<<<<<<<<<<")
        # print(sub_cat_href)
        # print(">>>>>>>test here 44444 <<<<<<<<<<<")
        # print(same_cat_href)
        if same_cat_href:
            yield Request(urljoin(response.url, same_cat_href), callback=self.parse_product_category_page,
                          meta={'id': product_id, 'type': PROD_TYPE, 'referrer': product_id})
        # print(">>>>>>>test here 11111 <<<<<<<<<<<")
        # print(manufact_flag, manufact_href)
        manufact_href = only_elem_or_default(manufact_href)
        # print(">>>>>>>test here 22222 <<<<<<<<<<<")
        # print(manufact_href)
        if manufact_href:
            if manufact_flag == 1:
                 # print(">>>>>>>test here 44444 <<<<<<<<<<<")
                 # print(manufact_flag)
                 yield Request(urljoin(response.url, manufact_href), callback=self.parse_product_manufact1_page,
                     meta={'id': product_id, 'type': PROD_TYPE, 'referrer': product_id})
            else:
                 yield Request(urljoin(response.url, manufact_href), callback=self.parse_product_manufact2_page,
                     meta={'id': product_id, 'type': PROD_TYPE, 'referrer': product_id})

        #yield the product reviews page.
        yield self._rev_page_request(product_id, PROD_TYPE)

    def parse_product_category_page(self, response):
        """
        Parses a page of same category products and yields products in the first page
        """
        self.logger.info('Parsing products of the same category as: %s' % response.meta['id'])
        settings = self.crawler.settings
        hxs = Selector(response)

        # if no significant element crawled, then try request it again to ensure that proxy really returned the target page
        # if not hxs.xpath('//body//h1[@id="zg_listTitle"]/text()'):
        #     yield Request(url=response.url, dont_filter=True)
        
        product_ids = hxs.xpath('//body//div[@id="zg_centerListWrapper"]//a[img]//@href').re(product_url_id_re)
        # print (">>>>>>>>>>>>>> product_ids<<<<<<<<<<<")
        # print(product_ids)
        n_same_cat = 0
        for product_id in product_ids:
            yield self._item_page_request(str(product_id), PROD_TYPE, referrer=response.meta['referrer'])
            n_same_cat += 1
            if n_same_cat > settings['SPIDER_MAX_SAME_CAT']:
                break
        # print (">>>>>>>>>>>>>> n_same_cat<<<<<<<<<<<")
        # print(n_same_cat)
        
    def parse_product_manufact1_page(self, response):
        """
        Parses a page of products of the same manufacturer and yields all the products in the first page
        """
        self.logger.info('Parsing products of the same manufacturer as: %s' % response.meta['id'])
        settings = self.crawler.settings
        hxs = Selector(response)
        # print(">>>>>>>test here 55555 <<<<<<<<<<<")

         # if no significant element crawled, then try request it again to ensure that proxy really returned the target page
        # if not hxs.xpath('//div[@id="leftNav"]//div[@class="shoppingEngineSectionHeaders"]/text()'):
        # if not hxs.xpath('//body//div[@id="mainResults"]//li//a[img]/@href'):
        #     yield Request(url=response.url, dont_filter=True)

        prod_ids = hxs.xpath('//body//div[@id="mainResults"]//li//a[img]/@href').re(product_url_id_re)
        # print (">>>>>>>>>>>>>> prod_ids<<<<<<<<<<<")
        # print(prod_ids)
        n_same_manufact = 0
        for prod_id in prod_ids:
            yield self._item_page_request(str(prod_id), PROD_TYPE, referrer=response.meta['referrer'])
            n_same_manufact += 1
            if n_same_manufact > settings['SPIDER_MAX_SAME_MANUFACT']:
                break
        # print (">>>>>>>>>>>>>> n_same_manufact<<<<<<<<<<<")
        # print(n_same_manufact)
        

    def parse_product_manufact2_page(self, response):
        """
        Parses a page of products of the same manufacturer and yields all the products in the first page
        """
        self.logger.info('Parsing products of the same manufacturer as: %s' % response.meta['id'])
        settings = self.crawler.settings
        hxs = Selector(response)
        
        # if not hxs.xpath('//body//h3/following-sibling::div//li/a/@href'):
        #     yield Request(url=response.url, dont_filter=True)

        prod_ids = hxs.xpath('//body//h3/following-sibling::div//li/a/@href').re(product_url_id_re)
        n_same_manufact = 0
        for prod_id in prod_ids:
            yield self._item_page_request(str(prod_id), PROD_TYPE, referrer=response.meta['referrer'])
            n_same_manufact += 1
            if n_same_manufact > settings['SPIDER_MAX_SAME_MANUFACT']:
                break

    
    def parse_product_rev_page(self, response):
        """
        parses a single product page and makes requests for subsequent pages
        """

        # Start parsing this page
        self.logger.info('Parsing product reviews: %s p%d' % (response.meta['id'], response.meta['page']))
        # from scrapy.shell import inspect_response
        # inspect_response(response)
        settings = self.crawler.settings
        hxs = Selector(response)

        # yield reviews and members posting them
        product_id = response.meta['id']

        # if not hxs.xpath('//div[contains(@class, "customerReviewsTitle")]/h1'):
        #     yield Request(url=response.url, dont_filter=True)

        revElems = hxs.xpath('//body//div[contains(@id, "review_list")]/div[@class="a-section review"]')
        for rev in revElems:
            # yield review info
            review = SingleValItemLoader(item=Review(), response=response)
            member_id = only_elem_or_default(rev.xpath('.//span[contains(text(), "By")]/following-sibling::a[contains(@href, "profile")]/@href').re(member_url_id_re))
            if member_id:
                member_id = str(member_id)
            star_rating_tmp = rev.xpath('.//i[contains(@class,"review-rating")]/span/text()').re(star_rating_re)
            if not star_rating_tmp:
                # It is probably a manufacturer response, not a review
                continue
            review.add_value('starRating', star_rating_tmp)
            # print (">>>>>>>>>>>>>> starRating<<<<<<<<<<<")
            # print(review._values['starRating'])
            review.add_value('id', rev.xpath('./@id').extract())
            # print (">>>>>>>>>>>>>> id <<<<<<<<<<<")
            # print(review._values['id'])
            review.add_value('productId', product_id)
            # print (">>>>>>>>>>>>>> productId<<<<<<<<<<<")
            # print(review._values['productId'])
            review.add_value('memberId', member_id)
            # print (">>>>>>>>>>>>>> memberId<<<<<<<<<<<")
            # print(review._values['memberId'])
            # nHelpful = rev.xpath('.//span[@class= "review-votes"]/text()').re(r'\w+\spersons?')
            nHelpful = rev.xpath('.//span[@class= "review-votes"]/text()').re(r'One|\d+')
            if nHelpful == ['One']:
                nHelpful = [u'1']
            # print (">>>>>>>>>>>>>> nHelpful<<<<<<<<<<<")
            # print(nHelpful)
            review.add_value('helpful', nHelpful)            
            review.add_value('title', rev.xpath('.//a[contains(@class, "review-title")]/text()').extract())
            # print (">>>>>>>>>>>>>> title<<<<<<<<<<<")
            # print(review._values['title'])
            review.add_value('date', rev.xpath('.//span[contains(@class, "review-date")]/text()').extract())
            # print (">>>>>>>>>>>>>> date<<<<<<<<<<<")
            # print(review._values['date'])
            review.add_value('verifiedPurchase', rev.xpath('.//span[contains(text(), "Verified Purchase")]'))
            # print (">>>>>>>>>>>>>> verifiedPurchase<<<<<<<<<<<")
            # print(review._values['verifiedPurchase'])
            review.add_value('reviewTxt', rev.xpath('.//span[contains(@class, "review-text")]/text()').extract())
            # print (">>>>>>>>>>>>>> reviewTxt<<<<<<<<<<<")
            # print(review._values['reviewTxt'])
            nComments_tmp = only_elem_or_default(rev.xpath('./div[contains(@class, "review-comments")]//span[contains(@class,"review-comment-total")]/following-sibling::span/text()').re(r'\d+comments?'), '0')
            review.add_value('nComments', nComments_tmp)
            # print (">>>>>>>>>>>>>> nComments<<<<<<<<<<<")
            # print(review._values['nComments'])
            review.add_value('vine', rev.xpath('.//span/b[contains(text(), "Customer review from the Amazon Vine Program")]'))
            review.add_value('timestamp', datetime.datetime.now().strftime(settings['TS_FMT']))
            yield review.load_item()

            # yield the reviewer
            yield self._item_page_request(member_id, MEMBER_TYPE, referrer=product_id)

        # request subsequent pages to be downloaded
        # Find out the number of review pages
        noPagesXPath = '(//body//ul[contains(@class,"pagination")]//li)[position()=last()-1]//a/text()'
        noPages = int(only_elem_or_default(hxs.xpath(noPagesXPath).re(r'\d+'), default='1'))
        if response.meta['page'] < noPages:
            yield self._successor_page_request(response)


    def start_requests(self):
        """
        read seed data from database

        """
        settings = self.crawler.settings
        reqs = []
        
        # connection = pymongo.MongoClient('localhost',27017);
        # db = connection[settings['MONGODB_SRC_DB']]
        # cursor = db['amznSpamTasks'].find({})
        # for seed in cursor:
        #     # forming the url for each seed ID
        #     itm_type = seed['jobType']
        #     itm_id = seed['amazonId']  
        #     try:
        #         # print("test start_requests()")
        #         req = self._item_page_request(itm_id, itm_type, referrer=None)
        #     except KeyError:
        #         raise ValueError("The type of seed with ID %s was %s. Expected 'p' or 'm'" % (itm_id, itm_type))
        #     reqs += arg_to_iter(req)
        # cursor.close()
        # return reqs

         # read seed data from seed.csv
         
        with open(settings['SPIDER_SEED_FILENAME'], 'r') as read_file:
            reader = csv.DictReader(read_file)
            for seed in reader:
                # forming the url for each seed ID
                # itm_type = seed['jobType']
                # itm_id = seed['amazonId']    
                itm_type = seed['Type']
                itm_id = seed['ID']             
                try:
                    # print("test start_requests()")
                    req = self._item_page_request(itm_id, itm_type, referrer=None)
                        # , referrer=None
                        # )
                except KeyError:
                    raise ValueError("The type of seed with ID %s was %s. Expected 'p' or 'm'" % (itm_id, itm_type))
                reqs += arg_to_iter(req)
        return reqs
