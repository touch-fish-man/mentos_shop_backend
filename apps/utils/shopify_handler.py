import contextlib
import os
import sys
import time
from collections import OrderedDict
from pprint import pprint
from pyquery import PyQuery
import logging

import django
import shopify

logger = logging.getLogger('pyactiveresource.connection')
logger.setLevel(logging.ERROR)

if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(os.path.join(base_dir, 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.prod")
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
django.setup()
from apps.products.models import *

# redis lrucache 装饰器
import json
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT


class LruCache:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.cache = cache

    def __call__(self, func):
        self.func = func
        return self

    def __get__(self, instance, owner):
        def wrapped_func(*args, **kwargs):
            key = f"{self.func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"
            value = cache.get(key)
            if value is None:
                value = self.func(instance, *args, **kwargs)
                cache.set(key, value, timeout=self.timeout)
            return value

        return wrapped_func


# logging.basicConfig(level=logging.DEBUG)


# scopes = ['read_products', 'read_orders']
# session = shopify.Session(shop_url, api_version, private_app_password)
# shopify.ShopifyResource.activate_session(session)


class ShopifyClient:
    def __init__(self, shop_url=None, api_key=None, api_scert=None, access_token=None, api_version=None):
        self.shop_url = shop_url
        self.api_version = api_version if api_version else '2023-01'
        self.api_key = api_key
        self.api_scert = api_scert
        self.access_token = access_token
        self.session = None
        self.check_shop()

    def check_shop(self):
        # 检查秘钥地址是否正确
        try:
            self.__get_session()
            shopify.Shop.current()
            return True
        except Exception as e:
            return False

    def __get_session(self):
        self.session = shopify.Session(self.shop_url, self.api_version, self.access_token)
        shopify.ShopifyResource.activate_session(self.session)
        return self.session

    @contextlib.contextmanager
    def get_session(self):
        if not self.session:
            self.__get_session()
        yield self.session

    @LruCache()
    def get_products(self, format=False):
        product_list = []
        for product in shopify.Product.find():
            if format:
                product_dict = self.format_product_info(product.to_dict())
            else:
                product_dict = product.to_dict()
            time.sleep(0.5)
            product_dict["product_collections"] = self.format_collection_info(product.collections())
            product_list.append(product_dict)
        return product_list

    def format_variant_info(self, variant):
        variant_info = {}
        variant_info["shopify_variant_id"] = variant['id']
        variant_info["variant_name"] = 'Default' if variant['title'] == 'Default Title' else variant['title']
        variant_info["variant_price"] = variant['price']
        variant_info["variant_stock"] = variant['inventory_quantity']
        variant_info["variant_option1"] = variant['option1'] if variant['option1'] else ""
        variant_info["variant_option2"] = variant['option2'] if variant['option2'] else ""
        variant_info["variant_option3"] = variant['option3'] if variant['option3'] else ""
        variant_info["variant_stock"] = 0
        variant_info["variant_desc"] = None
        variant_info["acl_group"] = {"id": None, "name": None}
        variant_info["server_group"] = {"id": None, "name": None}
        variant_info["cart_step"] = 8
        variant_info["is_active"] = True
        variant_info["proxy_time"] = 30
        return variant_info

    def format_product_info(self, product):
        product_info = {}
        product_info["product_name"] = product['title']
        product_info["shopify_product_id"] = product['id']
        tags = []
        for t in product['tags'].strip().split(','):
            tags.append({
                "tag_name": t.strip(),
                "tag_desc": ""
            })
        product_info["product_tags"] = tags
        try:
            product_info["product_desc"] = PyQuery(product['body_html']).text()
        except:
            product_info["product_desc"] = ""
        options = []
        for o in product['options']:
            values = []
            for v in o.get('values'):
                values.append({
                    "option_value": 'Default' if v == 'Default Title' else v,
                })
            if 'time' in o.get('name', ""):
                option_type = 1
            else:
                option_type = 0
            options.append({
                "option_name": "Default Option" if o.get('name') == "Title" else o.get('name'),
                "option_values": values,
                "shopify_option_id": o.get('id'),
                "option_type": option_type

            })
        product_info["variant_options"] = options
        product_info["variants"] = [self.format_variant_info(x) for x in product['variants']]
        return product_info

    def format_collection_info(self, collection):
        collection_list = []
        for x in collection:
            collection_info = {}
            collection_info["shopify_collection_id"] = x.id
            collection_info["collection_name"] = x.title
            try:
                collection_info["collection_desc"] = PyQuery(x.body_html).text()
            except:
                collection_info["collection_desc"] = ""
            collection_list.append(collection_info)
        return collection_list

    @LruCache()
    def get_product_collections(self):
        # 获取产品系列
        collection_list = []
        for collection in shopify.CustomCollection.find():
            dict_collection = {}
            dict_collection['id'] = collection.id
            dict_collection['title'] = collection.title
            try:
                dict_collection['desc'] = PyQuery(collection.body_html).text()
            except:
                dict_collection['desc'] = ""
            collection_list.append(dict_collection)
        return collection_list

    def get_product_tags(self):
        # 获取产品标签
        tag_list = []
        products = self.get_products()
        for product in products:
            tags = [x.strip() for x in product['tags'].strip().split(',')]
            for tag in tags:
                if tag not in tag_list:
                    tag_list.append(tag)
        return tag_list

    def get_product_variants(self, product_id, format=False):
        variant = shopify.Variant.find(product_id=product_id)
        variant_list = []
        for v in variant:
            if format:
                variant_list.append(self.format_variant_info(v.to_dict()))
            else:
                variant_list.append(v.to_dict())
        return variant_list

    def get_discounts(self):
        discount_list = []
        for discount in shopify.DiscountCode.find():
            discount_list.append(discount.to_dict())
        return discount_list

    def list_gift_cards(self):
        # 获取所有礼品卡
        # 需要开通shopify plus
        giftcards = shopify.GiftCard.find()
        giftcard_list = []
        for giftcard in giftcards:
            giftcard_list.append(giftcard.to_dict())
        return giftcard_list

    def list_price_rules(self):
        # 获取所有价格规则
        pricerules = shopify.PriceRule.find()
        pricerule_list = []
        for pricerule in pricerules:
            pricerule_list.append(pricerule.to_dict())
        return pricerule_list

    def list_orders(self):
        # 获取所有订单
        orders = shopify.Order.find(status='any', fields="id,note,email,financial_status,order_number",
                                    order="created_at DESC")
        order_list = []
        for order in orders:
            order_list.append(order.to_dict())
        return order_list

    def list_products(self):
        # 获取所有产品
        products = shopify.Product.find()
        product_list = []
        for product in products:
            product_list.append(product.to_dict())
        return product_list

    def list_product_variants(self):
        # 获取所有产品的所有变体
        variants = shopify.Variant.find()
        variant_list = []
        for variant in variants:
            variant_list.append(variant.to_dict())
        return variant_list

    def get_order_status(self, order_id):
        # 获取订单状态
        order = shopify.Order.find(status='any', ids=order_id, fields="id,note,email,financial_status")
        if order:
            return order[0].to_dict()
        else:
            return None

    @staticmethod
    def get_checkout_link(shop_url, data):
        base_url = shop_url + "cart/"

        cart_quantity_pairs = data.get("cart_quantity_pairs")
        email_str = "checkout[email]=" + data.get("email") if data.get("email") else ""
        note_str = "&note=" + data.get("note") if data.get("note") else ""
        discount_str = "&discount=" + data.get("discount") if data.get("discount") else ""
        ref_str = "&ref=" + data.get("ref") if data.get("ref") else ""
        access_token_str = "&access_token=" + data.get("access_token") if data.get("access_token") else ""
        attributes_str = ""
        for attr_name, attr_value in data.get("attributes").items():
            attributes_str += "&attributes[{}]={}".format(attr_name, attr_value)

        # 将cart_id和quantity分别存储在两个列表中
        cart_ids = []
        quantities = []
        for pair in cart_quantity_pairs:
            pair_split = pair.split(":")
            cart_ids.append(pair_split[0])
            quantities.append(pair_split[1])

        # 将多个cart_id和quantity拼接成字符串，用逗号隔开
        cart_quantity_str = ",".join([cart_ids[i] + ":" + quantities[i] for i in range(len(cart_ids))])

        url = base_url + cart_quantity_str + "?" + email_str + note_str + attributes_str + discount_str + ref_str + access_token_str
        return url

    def get_customers(self, args):
        customers = shopify.Customer.find(**args)
        customer_list = []
        for customer in customers:
            customer_list.append(customer.to_dict())
        return customer_list

    def list_customers(self):
        # 获取所有顾客
        args = {"limit": 250, "fields": "id,email,tags", "since_id": 0}
        customer_list = []
        while True:
            customers = self.get_customers(args)
            if customers:
                customer_list.extend(customers)
                args['since_id'] = customers[-1]['id']
            else:
                break
        customer_list = dict([(i['email'], i) for i in customer_list])
        return customer_list

    def create_customer(self, customer_info):
        # 创建顾客,用于同步网站注册用户到shopify
        # 用户名为邮箱
        customer = shopify.Customer()
        customer.email = customer_info['email']
        customer.phone = ""
        customer.verified_email = True
        customer.tags = customer_info['tags']
        customer.addresses = [
            {
                "address1": "",
                "city": "",
                "province": "",
                "phone": "",
                "zip": "",
                "last_name": "",
                "first_name": "",
                "country": ""
            }
        ]
        customer.note = "mentosproxy_web"
        return customer.save()

    def update_customer_tags(self, customer_info):
        # 更新顾客标签
        customer = shopify.Customer.find(customer_info['id'])
        customer.tags = customer_info['tags']
        return customer.save()

    def create_product(self, product_info):
        product = shopify.Product()
        product.title = product_info['title']
        try:
            product.body_html = PyQuery(product_info['body_html']).text()
        except:
            product.body_html = ""
        product.vendor = product_info['vendor']
        product.product_type = product_info['product_type']
        product.tags = product_info['tags']
        product.published = product_info['published']
        product.published_scope = product_info['published_scope']
        return product.save()

    def update_product(self, product_info):
        product = shopify.Product.find(product_info['id'])
        product.title = product_info['title']
        try:
            product.body_html = PyQuery(product_info['body_html']).text()
        except:
            product.body_html = ""
        product.vendor = product_info['vendor']
        product.product_type = product_info['product_type']
        product.tags = product_info['tags']
        product.published = product_info['published']
        product.published_scope = product_info['published_scope']
        product.save()
        return product.to_dict()

    def update_order(self, order_info):
        order = shopify.Order.find(order_info['id'])
        order.note = order_info['note']
        order.save()
        return order.to_dict()


class SyncClient(ShopifyClient):
    def __init__(self, *args, **kwargs):
        super(SyncClient, self).__init__(*args, **kwargs)

    def sync_customers(self):
        # 同步客户信息
        # 1. 获取本地所有客户
        # 2. 更新客户信息到shopify
        # 3. 更新客户等级
        from apps.users.models import User
        all_users = User.objects.all()
        shopify_users = self.list_customers()
        for user in all_users:
            email = str(user.email).lower()
            if email in shopify_users:
                if "vip" + str(user.level) != shopify_users[email]['tags']:
                    # 更新用户等级
                    shopify_users[email]['tags'] = "vip" + str(user.level)
                    logging.info("update customer {} tags to {}".format(email, shopify_users[email]['tags']))
                    self.update_customer_tags(shopify_users[email])
                    time.sleep(0.5)
            else:
                # 创建用户
                customer_info = {
                    "first_name": user.username,
                    "last_name": user.username,
                    "email": email,
                    "tags": "vip" + str(user.level)
                }
                self.create_customer(customer_info)
                logging.info("create customer {}".format(email))
                # 增加请求频率限制
                time.sleep(0.5)

    def update_customer_tags_by_email(self, email, tags):
        # 更新顾客标签
        email = str(email).lower()
        try:
            customer = shopify.Customer.find(email=email)[0]
        except:
            return
        customer.tags = tags
        return customer.save()

    def add_user_to_customer(self, email):
        from apps.users.models import User
        user = User.objects.filter(email=email).first()
        if user:
            # 添加用户到shopify客户
            customer_info = {
                "first_name": user.username,
                "last_name": user.username,
                "email": user.email,
                "tags": "vip" + str(user.level)
            }
            self.create_customer(customer_info)

    def sync_customer_tags(self):
        # 同步客户标签 更新用户等级
        pass

    def sync_customer_orders(self):
        # 同步客户订单
        pass

    def sync_products(self):
        # 同步产品
        pass

    def sync_product_variants(self):
        # 同步产品变体
        pass

    def sync_product_collections(self):
        collection_list = self.get_product_collections()
        for i in collection_list:
            if ProductCollection.objects.filter(collection_name=i['title']).exists():
                ProductCollection.objects.filter(collection_name=i['title']).update(collection_desc=i['desc'])
                ProductCollection.objects.filter(collection_name=i['title']).update(soft_delete=False)
            else:
                ProductCollection.objects.create(collection_name=i['title'], collection_desc=i['desc'],
                                                 shopify_collection_id=i['id'])
        # 删除本地数据库中不存在的标签
        for collection in ProductCollection.objects.filter(soft_delete=True).exclude(
                collection_name__in=[i['title'] for i in collection_list]).all():
            if ProductCollectionRelation.objects.filter(product_collection=collection.id).exists():
                # 如果标签被产品使用，则不删除
                continue
            collection.delete()
        return True

    def sync_product_tags(self):
        # 同步产品标签
        # 从shopify获取所有产品，插入到本地数据库
        tag_list = self.get_product_tags()
        for tag in tag_list:
            query_ret = ProductTag.objects.filter(tag_name=tag).first()
            if query_ret:
                query_ret.soft_delete = False
                query_ret.save()
            else:
                ProductTag.objects.create(tag_name=tag)
        # 删除本地数据库中不存在的标签
        for tag in ProductTag.objects.filter(soft_delete=True).exclude(tag_name__in=tag_list).all():
            if ProductTagRelation.objects.filter(product_tag=tag.id).exists():
                # 如果标签被产品使用，则不删除
                continue
            tag.delete()
        return True

    def sync_shopify(self, customers=False, products=True):
        # 同步shopify
        if customers:
            self.sync_customers()
        if products:
            self.sync_product_collections()
            self.sync_product_tags()

    def sync_promotions(self):
        # 同步促销
        pass

    def sync_orders(self):
        # 同步订单
        pass


if __name__ == '__main__':
    shop_url = 'https://mentosproxy.myshopify.com/'
    api_key = 'dd6b4fd6efe094ef3567c61855f11385'
    api_scert = 'f729623ef6a576808a5e83d426723fc1'
    private_app_password = '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'
    SHOPIFY_SHOP_URL = 'https://mentosproxy-2.myshopify.com/'
    SHOPIFY_APP_KEY = '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'
    SHOPIFY_API_KEY = '07616114a90f98723b476cc38ad7f22a'
    SHOPIFY_API_SECRET = 'c22837d6d8e9332ee74e2106037bcb37'
    SHOPIFY_WEBHOOK_KEY = 'de1bdf66588813b408d1e9e335ba67522b3fe8e776f0e5f22fbf4ad1863d789e'
    # shopify_client = SyncClient(shop_url, api_version, api_key, api_scert, private_app_password)

    # for product in shopify_client.get_products(format=True):
    #     pprint(product)
    #
    # # pprint(shopify_client.list_orders())
    # # pprint(shopify_client.get_order_status("5327981838646"))
    # # pprint(shopify_client.get_customers())
    # # 创建客户
    #
    # customer_info = {
    #     "first_name": "test",
    #     "last_name": "test",
    #     "email": "tes2t@test.com",
    #     "tags": "vip2"
    # }
    # pprint(shopify_client.create_customer(customer_info))
    # pprint(shopify_client.get_product_collections())
    # pprint(shopify_client.get_product_tags())
    # pprint(shopify_client.get_customers())

    syncclient = SyncClient(SHOPIFY_SHOP_URL, SHOPIFY_API_KEY, SHOPIFY_API_SECRET, SHOPIFY_APP_KEY)
    # print(syncclient.sync_product_collections())
    # print(syncclient.sync_product_tags())
    # print(syncclient.get_customers())
    # syncclient.update_customer_tags_by_email('test@test.com', 'vip10')
