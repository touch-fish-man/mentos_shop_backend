import contextlib
import time
from pprint import pprint

import shopify

shop_url = 'https://mentosproxy.myshopify.com/'
api_version = '2023-01'
api_key = 'dd6b4fd6efe094ef3567c61855f11385'
api_scert = 'f729623ef6a576808a5e83d426723fc1'
private_app_password = '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'

import logging

logging.basicConfig(level=logging.DEBUG)


# scopes = ['read_products', 'read_orders']
# session = shopify.Session(shop_url, api_version, private_app_password)
# shopify.ShopifyResource.activate_session(session)


class ShopifyClient:
    def __init__(self, shop_url, api_version, api_key, api_scert, access_token):
        self.shop_url = shop_url
        self.api_version = api_version
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

    def get_products(self):
        product_list = []
        for product in shopify.Product.find():
            product_list.append(product.to_dict())
        return product_list

    def get_product_collections(self):
        # 获取产品系列
        collection_list = []
        for collection in shopify.CustomCollection.find():
            collection_list.append(collection.to_dict())
        return collection_list

    def get_product_tags(self):
        # 获取产品标签
        tag_list = []
        for tag in shopify.Product.find():
            tag_list.append(tag.to_dict())
        return tag_list

    def get_product_variants(self, product_id):
        variant = shopify.Variant.find(product_id=product_id)
        variant_list = []
        for v in variant:
            variant_list.append(v.to_dict())
        return variant_list

    def get_discounts(self):
        discount_list = []
        for discount in shopify.DiscountCode.find():
            discount_list.append(discount.to_dict())
        return discount_list

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

    def gen_permalink(self, data):
        base_url = self.shop_url + "/cart/clear?return_to=/cart/"

        cart_quantity_pairs = data.get("cart_quantity_pairs")
        email = data.get("email")
        note = data.get("note")
        discount = data.get("discount")
        ref = data.get("ref")

        # 将cart_id和quantity分别存储在两个列表中
        cart_ids = []
        quantities = []
        for pair in cart_quantity_pairs:
            pair_split = pair.split(":")
            cart_ids.append(pair_split[0])
            quantities.append(pair_split[1])

        # 将多个cart_id和quantity拼接成字符串，用逗号隔开
        cart_quantity_str = ",".join([cart_ids[i] + ":" + quantities[i] for i in range(len(cart_ids))])

        url = base_url + cart_quantity_str + "?checkout[email]=" + email + "&note=" + note + "&discount=" + discount + "&ref=" + ref
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


class SyncClient:
    def sync_customers(self):
        # 同步客户信息
        pass

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

    def sync_product_tags(self):
        # 同步产品标签
        pass

    def sync_promotions(self):
        # 同步促销
        pass

    def sync_orders(self):
        # 同步订单
        pass


if __name__ == '__main__':
    shopify_client = ShopifyClient(shop_url, api_version, api_key, api_scert, private_app_password)
    # for product in shopify_client.get_products():
    #     pprint(product)
    # pprint(shopify_client.list_orders())
    # pprint(shopify_client.get_order_status("5327981838646"))
    # pprint(shopify_client.get_customers())
    # 创建客户
    customer_info = {
        "first_name": "test",
        "last_name": "test",
        "email": "tes2t@test.com",
        "tags": "vip2"
    }
    # pprint(shopify_client.create_customer(customer_info))
    pprint(shopify_client.get_product_collections())
    # pprint(shopify_client.get_customers())
