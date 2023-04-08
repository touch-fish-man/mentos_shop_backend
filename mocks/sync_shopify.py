import random
import string

from faker import Faker
import os
import sys

from init_env import *
from rich.console import Console

console = Console()
from apps.utils.shopify_handler import SyncClient
from django.conf import settings



def main():
    with console.status("[bold green]Syncing shopify...") as status:
        print("Syncing shopify...")
        shop_url = settings.SHOPIFY_SHOP_URL
        api_key = settings.SHOPIFY_API_KEY
        api_scert = settings.SHOPIFY_API_SECRET
        shopify_app_key = settings.SHOPIFY_APP_KEY
        sync_client = SyncClient(shop_url, api_key, api_scert, shopify_app_key)
        sync_client.sync_shopify()

if __name__ == '__main__':
    main()