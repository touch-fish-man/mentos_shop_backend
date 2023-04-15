
from init_env import *
from rich.console import Console
import random
import string

from faker import Faker
import os
import sys
console = Console()

from apps.products.models import Product, ProductCollection, ProductTag
from apps.utils.shopify_handler import ShopifyClient,SyncClient
from apps.proxy_server.models import AclGroup,ServerGroup
from apps.products.serializers import OptionSerializer, VariantCreateSerializer, ProductCollectionSerializer, \
    ProductTagSerializer
from django.conf import settings

fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating product...") as status:
        sync_client = SyncClient(settings.SHOPIFY_SHOP_URL, settings.SHOPIFY_API_KEY, settings.SHOPIFY_API_SECRET, settings.SHOPIFY_APP_KEY)
        sync_client.sync_product_tags()
        sync_client.sync_product_collections()
        products_list = sync_client.get_products(format=True)
        for product in products_list:
            variants_data = product.pop('variants')
            product_collections_data = product.pop('product_collections')
            product_tags_data = product.pop('product_tags')
            options_data = product.pop('variant_options')
            acl_group = random.choice(AclGroup.objects.all())
            server_group = random.choice(ServerGroup.objects.all())
            product = Product.objects.create(**product)
            # 创建option
            for option_data in options_data:
                option_data['product'] = product
                OptionSerializer().create(option_data)  # 创建variant
            for variant_data in variants_data:
                variant_data["variant_desc"]=fake.sentence(nb_words=6, variable_nb_words=True, ext_word_list=None)
                variant_data["acl_group"]= acl_group
                variant_data["server_group"]= server_group
                variant_data['product'] = product
                variant_data['proxy_time'] = random.randint(1, 100)
                VariantCreateSerializer().create(variant_data)
            # 创建product_collection
            for product_collection_data in product_collections_data:
                product_collection = ProductCollectionSerializer().create(product_collection_data)
                product.product_collections.add(product_collection)
            # 创建product_tag
            for product_tag_data in product_tags_data:
                product_tag = ProductTagSerializer().create(product_tag_data)
                product.product_tags.add(product_tag)
            product.save()
if __name__ == '__main__':
    main()
