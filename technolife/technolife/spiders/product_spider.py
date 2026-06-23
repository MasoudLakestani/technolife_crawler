import re
import os
import json
import base64
import scrapy
import logging
import datetime
import jdatetime
from itertools import cycle
from technolife.items import *
from scrapy.exceptions import DontCloseSpider
from scrapy_redis.spiders import RedisSpider

class ProductsSpider(RedisSpider):

    name = "technolifeProduct"
    allowed_domains = ["www.technolife.com"]
    handle_httpstatus_list = [404]
    redis_batch_size = 10
    logger = logging.getLogger()
    redis_key = 'technolifeProduct:first_crawl'
    technolife_affiliate_link = "https://deemanetwork.com/click/d/4b7888df_e8ae_42e1_916a_33172459d735"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        redis_keys_env = os.getenv("REDIS_KEYS", "first_crawl")
        self.redis_keys_priority = cycle([f"technolifeProduct:{key.strip()}" for key in redis_keys_env.split(",")])
        self.redis_key = next(self.redis_keys_priority)
        print(self.redis_key)

    def urlsafe_base64_encode(self, url: str) -> str:
        return base64.urlsafe_b64encode(
            url.encode("utf-8")
        ).decode("utf-8").rstrip("=")
    
    def pop_list_queue(self, redis_key, batch_size):
        datas = super().pop_list_queue(redis_key, batch_size)
        if not datas:
            self.redis_key = next(self.redis_keys_priority)
            self.logger.info(f"Change Redis key: {self.redis_key}")
        return datas
    
    def update_price(self, updating_variant, prices):
        today_jdate = jdatetime.date.today()
        today_str = today_jdate.strftime("%Y-%m-%d")
        new_rrp = prices["rrp_price"]
        new_selling = prices["selling_price"]
        discount_percent = prices["discount_percent"]
        current_price_data = {
                    "rrp_price": new_rrp, 
                    "selling_price": new_selling,
                    "discount_percent": discount_percent
                }

        price_history = updating_variant["price_history"]

        last_date_str = list(price_history.get("end_price", {}).keys())[0]
        last_prices = price_history.get("end_price", {}).get(last_date_str, {})
        
        price_changed = (new_rrp != last_prices.get("rrp_price") or 
                    new_selling != last_prices.get("selling_price"))
        
        if price_changed:
            if "middle_prices" not in price_history:
                price_history["middle_prices"] = {}
            price_history["middle_prices"][last_date_str] = last_prices
            price_history["middle_prices"][today_str] = current_price_data
            
            price_history["end_price"] = {today_str: current_price_data}
        else:
            price_history["end_price"] = {today_str: current_price_data}
        

        start_date_str = list(price_history.get("start_price", {}).keys())[0]
        start_jdate = jdatetime.date(*map(int, start_date_str.split("-")))
        days_diff = (today_jdate - start_jdate).days
        
        if days_diff > 180:
            start_price_data = price_history["start_price"][start_date_str]
            last_price = start_price_data
            if price_history.get("middle_prices"):
                middle_dates = sorted(price_history["middle_prices"].keys())
                suitable_date = None
                
                for date_str in middle_dates:
                    date_obj = jdatetime.date(*map(int, date_str.split("-")))
                    gap = (today_jdate - date_obj).days
                    
                    if gap > 180:
                        if gap > 180 and gap < days_diff:
                            last_price =  price_history["middle_prices"][date_str]
                        del price_history["middle_prices"][date_str]
                    if gap == 180:
                        suitable_date = date_str
                        break
                
                if suitable_date:
                    price_history["start_price"] = {suitable_date: price_history["middle_prices"][suitable_date]}
                    del price_history["middle_prices"][suitable_date]
                else:
                    target_days_back = 180
                    new_start_date = today_jdate - datetime.timedelta(days=target_days_back)
                    new_start_date_str = new_start_date.strftime("%Y-%m-%d")
                    price_history["start_price"] = {new_start_date_str: last_price}
            else:
                target_days_back = 180
                new_start_date = today_jdate - datetime.timedelta(days=target_days_back)
                new_start_date_str = new_start_date.strftime("%Y-%m-%d")
                price_history["start_price"] = {new_start_date_str: last_price}
        # Collect all price points with dates
        price_points = []
        for section in ["start_price", "middle_prices", "end_price"]:
            for date_str, prices in price_history.get(section, {}).items():
                if prices["selling_price"]:
                    price_points.append((date_str, prices["selling_price"]))

        # Sort by date to ensure chronological order
        price_points.sort(key=lambda x: x[0])

        if len(price_points) == 0:
            mean_price = 0
        elif len(price_points) == 1:
            mean_price = price_points[0][1]
        else:
            # Calculate time-weighted average
            total_weighted_price = 0
            total_days = 0

            for i in range(len(price_points) - 1):
                current_date_str, current_price = price_points[i]
                next_date_str, _ = price_points[i + 1]

                # Parse jalali dates
                current_date = jdatetime.date(*map(int, current_date_str.split("-")))
                next_date = jdatetime.date(*map(int, next_date_str.split("-")))

                # Calculate days this price was active
                days = (next_date - current_date).days

                total_weighted_price += current_price * days
                total_days += days

            # Add the last price period (from last date to today)
            last_date_str, last_price = price_points[-1]
            last_date = jdatetime.date(*map(int, last_date_str.split("-")))
            days_to_today = (today_jdate - last_date).days

            total_weighted_price += last_price * days_to_today
            total_days += days_to_today

            mean_price = total_weighted_price / total_days if total_days > 0 else 0

        updating_variant["mean_of_prices"] = mean_price

        updating_variant["price_history"] = price_history
        return(updating_variant)
    
    def process_variants(self, merged_variants, existing_variants):

        today_jdate = jdatetime.date.today()
        today_str = today_jdate.strftime("%Y-%m-%d")
        ids = [item["id"] for item in existing_variants]

        for variant in merged_variants:
            keep_keys = {"price", "discounted_price", "discount"}
            prices = {
                k: (v * 10 if k in {"price", "discounted_price"} else v)
                for k, v in variant.items()
                if k in keep_keys
            }
            discount = 0
            if prices["discount"]:
                discount = int(prices["discount"].replace("%",""))
            current_price_data = {
                    "rrp_price": prices["price"], 
                    "selling_price":  prices["discounted_price"],
                    "discount_percent": discount
                }
            prices = current_price_data
            variant_id = int(variant["_id"][-4:], 16)
                
            if variant_id in ids:
                ids.remove(variant_id)
                updating_variant = next(
                    (existing_variants.pop(i) for i, item in enumerate(existing_variants) if item["id"] == variant_id),
                    None
                )
                updating_variant = self.update_price(updating_variant, prices)
                existing_variants.append(updating_variant)
                
            else:
                new_variant = {}
                price_history = {
                    "start_price": {today_str: current_price_data},
                    "middle_prices": {},
                    "end_price": {today_str: current_price_data}
                }
                new_variant["id"] = variant_id
                new_variant["price_history"] = price_history
                new_variant["mean_of_prices"] = current_price_data["selling_price"]
                existing_variants.append(new_variant)

        if len(ids) != 0:
            for id in ids:
                updating_variant = next(
                    (existing_variants.pop(i) for i, item in enumerate(existing_variants) if item["id"] == id),
                    None
                )
                prices = {
                    "rrp_price":None,
                    "selling_price":None,
                    "discount_percent":0
                }
                updating_variant = self.update_price(updating_variant, prices)
                existing_variants.append(updating_variant)

        return existing_variants

    def parse(self, response):
        try:
            existing_variants = response.meta.get("variants")
            request_count = response.meta.get("request_count")
            created_date = response.meta.get("created_date")
            number_of_inactivity = response.meta.get("number_of_inactivity")
            user_like = response.meta.get("user_like")
            user_dislike = response.meta.get("user_dislike")
            is_vectorized = response.meta.get("is_vectorized")
            base64_encoded_product_url = self.urlsafe_base64_encode(response.url)

            if is_vectorized == None:
                is_vectorized = False
            # Extract product ID from URL
            match = re.search(r'product-(\d+)', response.url)
            if match:
                product_id = match.group(1)
            else:
                logging.error(f"Could not extract product ID from URL: {response.url}")
                return

            script_pattern = r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>'
            script_match = re.search(script_pattern, response.text, re.DOTALL)


            # Parse the JSON data
            json_str = script_match.group(1)
            jsondata = json.loads(json_str)

            # Extract data from the JSON structure
            pageProps = jsondata.get('props', {}).get('pageProps', {})
            queries = pageProps.get('dehydratedState', {}).get('queries', [])
            product_info = queries[0].get('state', '').get('data', '').get('product_info', '')
            categories_data = queries[1]

            product = ProductItem()
            product["uuid"] = product_id
            product["dbid"] = f"technolife-{product_id}"
            product["title_fa"] = product_info.get('title', '')
            product["title_en"] = None
            product["supply_category"] = None

            middle_items = categories_data.get('state', '').get('data', '')[1:]
            categories = [None]*5     

            for i, item in enumerate(middle_items):
                if i < 5:
                    categories[i] = item["name"]

            category1, category2, category3, category4, category5 = categories
            # product["category1"] = category1
            # product["category2"] = category2
            # product["category3"] = category3
            # product["category4"] = category4
            # product["category5"] = category5
            product["category1"] = None
            product["category2"] = None
            product["category3"] = None
            product["category4"] = None
            product["category5"] = None     

            product["brand"] = {
                    "title_fa": product_info["brand"]["name"],
                    "title_en": product_info["brand"]["enName"],
                }
            product["description"] = None
            product["is_fake"] = False
            product["admin_marked_fake"] = False
            product["url"] = f"{self.technolife_affiliate_link}/{base64_encoded_product_url}"
            product["website"] = {
                "title": "technolife",
                "url": "www.technolife.com"
            }
            main_image =  product_info.get('main_image', '')
            if main_image:
                image = main_image.get('image', '')
            else: 
                image = product_info.get('color_items', '')[0].get('image', '').get('image', '')

            product["image_url"] = [f"{product["website"]["url"]}{image}"]
            product["is_active"] = False
            product["created_date"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            product["updated_date"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            if created_date:
                product["created_date"] = created_date
            product["user_like"] = user_like
            product["user_dislike"] = user_dislike

            product["is_active"] = product_info.get('is_available', '')
            product["number_of_inactivity"] = number_of_inactivity + 1
            if product["is_active"]:
                product["number_of_inactivity"] = 0
            
            merged_variants =  product_info.get('color_items', '')
            processed_variants = self.process_variants(merged_variants, existing_variants)
            product["variants"] = processed_variants
            best_price = {
                "id": None,
                "end_price": {},
                "mean_of_prices": None
            }

            if processed_variants and product["is_active"]:

                selling_prices = [
                    list(x["price_history"]["end_price"].values())[0]["selling_price"]
                    for x in processed_variants
                    if list(x["price_history"]["end_price"].values())[0]["selling_price"] is not None
                ]
                
                min_price = min(selling_prices)
                max_price = max(selling_prices)

                price_diff_percent = ((max_price - min_price) / min_price) * 100 if min_price > 0 else 0
                if price_diff_percent > 20:

                    max_discount = max(
                        list(x["price_history"]["end_price"].values())[0]["discount_percent"]
                        for x in processed_variants
                        if list(x["price_history"]["end_price"].values())[0]["discount_percent"] is not None
                    )

                    candidates = [
                        x for x in processed_variants
                        if (
                            list(x["price_history"]["end_price"].values())[0]["discount_percent"] is not None
                            and list(x["price_history"]["end_price"].values())[0]["discount_percent"] == max_discount
                        )
                    ]

                    best_item = min(
                        (x for x in candidates if list(x["price_history"]["end_price"].values())[0]["selling_price"] is not None),
                        key=lambda x: list(x["price_history"]["end_price"].values())[0]["selling_price"]
                    )

                else:

                    best_item = min(
                        (x for x in processed_variants if list(x["price_history"]["end_price"].values())[0]["selling_price"] is not None),
                        key=lambda x: list(x["price_history"]["end_price"].values())[0]["selling_price"]
                    )

                best_price = {
                    "id": best_item["id"],
                    "end_price": best_item["price_history"]["end_price"],
                    "mean_of_prices": best_item["mean_of_prices"]
                }

            if best_price["end_price"] and product["is_active"]:
                best_price_value = list(best_price["end_price"].values())[0]

                product["selling_price"] = best_price_value["selling_price"]
                product["rrp_price"] = best_price_value["rrp_price"]
                product["discount_percent"] = best_price_value["discount_percent"]
                product["variant_id"] = best_price["id"]
                product["mean_of_prices"] = best_price["mean_of_prices"]
            else:
                # fallback values when no variants exist
                product["selling_price"] = None
                product["rrp_price"] = None
                product["discount_percent"] = None
                product["variant_id"] = None
                product["mean_of_prices"] = None
            product["scam_score"] = 0
            yield product

        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error for product {product_id}: {str(e)}")
        except Exception as e:
            logging.error(f"Error processing URL {response.url}: {str(e)}")
            raise DontCloseSpider