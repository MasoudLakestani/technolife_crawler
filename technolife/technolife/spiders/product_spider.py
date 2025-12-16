import os
import scrapy
import base64
import logging
import datetime
from itertools import cycle
import jdatetime
from technolife.items import *
from scrapy.exceptions import DontCloseSpider
from scrapy_redis.spiders import RedisSpider

class ProductsSpider(RedisSpider):

    name = "technolifeProduct"
    allowed_domains = ["api.digikala.com"]
    handle_httpstatus_list = [404]
    redis_batch_size = 128
    logger = logging.getLogger()
    redis_key = 'technolifeProduct:first_crawl'

    def parse(self, response):
        try:
            jsonresponse = response.json()
            existing_variants = response.meta.get("variants")
            request_count = response.meta.get("request_count")
            created_date = response.meta.get("created_date")
            number_of_inactivity = response.meta.get("number_of_inactivity")
            user_like = response.meta.get("user_like")
            user_dislike = response.meta.get("user_dislike")

            product = ProductItem()
            product["uuid"] = jsonresponse["data"]["product"]["id"]
            product["dbid"] = f"technolife-{product["uuid"]}"
            product["title_fa"] = jsonresponse["data"]["product"]["title_fa"]
            product["title_en"] = jsonresponse["data"]["product"]["title_en"]
            product["supply_category"] = jsonresponse["data"]["intrack"]["eventData"]["supplyCategory"]
        
        except Exception as e:
            # add log that what is the error.
            logging.error(f"Error processing URL {response.url}: {str(e)}")
            raise DontCloseSpider