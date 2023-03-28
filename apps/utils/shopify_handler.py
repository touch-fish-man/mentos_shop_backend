import contextlib
from pprint import pprint

import shopify

shop_url = 'https://asadad22222.myshopify.com'
api_version = '2023-01'
api_key = '7e475db3903d1e869c97ff08d04734dc'
api_scert = '686605b1817df531679842832848c34b'
private_app_password = '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'


# scopes = ['read_products', 'read_orders']
# session = shopify.Session(shop_url, api_version, private_app_password)
# shopify.ShopifyResource.activate_session(session)


# 查询产品
# products = shopify.Product.find()
# print(products)
# 创建产品
# product = shopify.Product()
# product.title = 'Burton Custom Freestyle 151'
# product.product_type = 'Snowboard'
# product.vendor = 'Burton'
# product.save()
# print(product)

class ShopifyClient:
    def __init__(self, shop_url, api_version, api_key, api_scert, private_app_password):
        self.shop_url = shop_url
        self.api_version = api_version
        self.api_key = api_key
        self.api_scert = api_scert
        self.private_app_password = private_app_password
        self.session = None

    def __get_session(self):
        self.session = shopify.Session(shop_url, api_version, private_app_password)
        shopify.ShopifyResource.activate_session(self.session)
        return self.session

    @contextlib.contextmanager
    def get_session(self):
        if not self.session:
            self.__get_session()
        yield self.session

    def get_products(self):
        with self.get_session() as session:
            return shopify.Product.find()

    def get_orders(self):
        return shopify.Order.find()

    def get_customers(self):
        return shopify.Customer.find()

    def get_webhooks(self):
        return shopify.Webhook.find()

    def get_shop(self):
        return shopify.Shop.current()

    def generate_cart_url(self,data):
        base_url = self.shop_url+"/cart/clear?return_to=/cart/"

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
    def create_product(self, **kwargs):
        return shopify.Product.create(**kwargs)


if __name__ == '__main__':
    shopify_client = ShopifyClient(shop_url, api_version, api_key, api_scert, private_app_password)
    for product in shopify_client.get_products():
        # 打印产品信息
        pprint(product.to_dict())
    # 创建产品
    shopify_client.create_product()
