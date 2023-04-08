import contextlib
import os
import sys
import time
from collections import OrderedDict
from pprint import pprint

import django
import shopify

if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(base_dir)
    if os.path.exists(os.path.join(base_dir, 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()
from apps.products.models import *


import logging


# logging.basicConfig(level=logging.DEBUG)


# scopes = ['read_products', 'read_orders']
# session = shopify.Session(shop_url, api_version, private_app_password)
# shopify.ShopifyResource.activate_session(session)


class ShopifyClient:
    def __init__(self, shop_url=None, api_key=None, api_scert=None, access_token=None,api_version=None):
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

    def get_products(self, format=False):
        product_list = []
        for product in shopify.Product.find():

            if format:
                product_dict = self.format_product_info(product.to_dict())
            else:
                product_dict = product.to_dict()
            product_dict["product_collections"] = self.format_collection_info(product.collections())
            product_list.append(product_dict)
        return product_list

    def format_variant_info(self, variant):
        variant_info = {}
        variant_info["shopify_variant_id"] = variant['id']
        variant_info["variant_name"] = variant['title']
        variant_info["variant_price"] = variant['price']
        variant_info["variant_stock"] = variant['inventory_quantity']
        variant_info["variant_option1"] = variant['option1'] if variant['option1'] else ""
        variant_info["variant_option2"] =  variant['option2'] if variant['option2'] else ""
        variant_info["variant_option3"] = variant['option3'] if variant['option3'] else ""
        return variant_info

    def format_product_info(self, product):
        product_info = {}
        product_info["product_name"] = product['title']
        product_info["shopify_product_id"] = product['id']
        tags = []
        for t in product['tags'].split(','):
            tags.append({
                "tag_name": t,
                "tag_desc": ""
            })
        product_info["product_tags"] = tags
        product_info["product_desc"] = product['body_html']
        options = []
        for o in product['options']:
            values = []
            for v in o.get('values'):
                values.append({
                    "option_value": v,
                })
            options.append({
                "option_name": o.get('name'),
                "option_values": values,
                "shopify_option_id": o.get('id'),
                "option_type": ""

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
            collection_info["collection_desc"] = x.body_html
            collection_list.append(collection_info)
        return collection_list

    def get_product_collections(self):
        # 获取产品系列
        collection_list = []
        for collection in shopify.CustomCollection.find():
            dict_collection = {}
            dict_collection['id'] = collection.id
            dict_collection['title'] = collection.title
            dict_collection['desc'] = collection.body_html
            collection_list.append(dict_collection)
        return collection_list

    def get_product_tags(self):
        # 获取产品标签
        tag_list = []
        products=self.get_products()
        for product in products:
            tags = product['tags'].split(',')
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
        orders = shopify.Order.find(status='any', fields="id,note,email,financial_status", order="created_at DESC")
        order_list = []
        for order in orders:
            order_list.append(order.to_dict())
        return order_list

    def list_customers(self):
        # 获取所有顾客
        customers = shopify.Customer.find()
        customer_list = []
        for customer in customers:
            customer_list.append(customer.to_dict())
        return customer_list

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
        base_url = shop_url + "/cart/clear?return_to=/cart/"

        cart_quantity_pairs = data.get("cart_quantity_pairs")
        email = data.get("email")
        note = data.get("note")
        discount_str = "&discount=" + data.get("discount") if data.get("discount") else ""
        ref_str = "&ref=" + data.get("ref") if data.get("ref") else ""

        # 将cart_id和quantity分别存储在两个列表中
        cart_ids = []
        quantities = []
        for pair in cart_quantity_pairs:
            pair_split = pair.split(":")
            cart_ids.append(pair_split[0])
            quantities.append(pair_split[1])

        # 将多个cart_id和quantity拼接成字符串，用逗号隔开
        cart_quantity_str = ",".join([cart_ids[i] + ":" + quantities[i] for i in range(len(cart_ids))])

        url = base_url + cart_quantity_str + "?checkout[email]=" + email + "&note=" + note + discount_str + ref_str
        return url

    def get_customers(self):
        customers = shopify.Customer.find()
        customer_list = []
        for customer in customers:
            customer_list.append(customer.to_dict())
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
        return customer.save()

    def create_product(self, product_info):
        product = shopify.Product()
        product.title = product_info['title']
        product.body_html = product_info['body_html']
        product.vendor = product_info['vendor']
        product.product_type = product_info['product_type']
        product.tags = product_info['tags']
        product.published = product_info['published']
        product.published_scope = product_info['published_scope']
        return product.save()

    def update_product(self, product_info):
        product = shopify.Product.find(product_info['id'])
        product.title = product_info['title']
        product.body_html = product_info['body_html']
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
        shopify_users=self.get_customers()
        shopify_users_email_dict=dict([(i['email'],i) for i in shopify_users])
        for user in all_users:
            if not (user.email in shopify_users_email_dict and "vip"+str(user.level)==shopify_users_email_dict[user.email]['tags']):
                print(user.email)
                # 创建用户
                customer_info = {
                    "first_name": user.username,
                    "last_name": user.username,
                    "email": user.email,
                    "tags": "vip"+str(user.level)
                }
                self.create_customer(customer_info)
                # 增加请求频率限制
                time.sleep(1)

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
        collection_list=self.get_product_collections()
        for i in collection_list:
            if ProductCollection.objects.filter(collection_name=i['title']).exists():
                ProductCollection.objects.filter(collection_name=i['title']).update(collection_desc=i['desc'])
            else:
                ProductCollection.objects.create(collection_name=i['title'],collection_desc=i['desc'])
        return True

    def sync_product_tags(self):
        # 同步产品标签
        # 从shopify获取所有产品，插入到本地数据库
        tag_list=self.get_product_tags()
        for tag in tag_list:
            if ProductTag.objects.filter(tag_name=tag).exists():
                continue
            else:
                ProductTag.objects.create(tag_name=tag)
        return True


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

    syncclient = SyncClient(shop_url, api_key, api_scert, private_app_password)
    # print(syncclient.sync_product_collections())
    # print(syncclient.sync_product_tags())
    # print(syncclient.get_customers())
    print(syncclient.sync_customers())