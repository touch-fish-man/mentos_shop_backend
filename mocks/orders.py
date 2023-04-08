import random
import string

from faker import Faker
import os
import sys

from init_env import *
from rich.console import Console

console = Console()

from apps.orders.models import Orders
from apps.users.models import User
from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating orders...") as status:
        # Orders.objects.all().delete()
        print("Generating orders...")
        for i in range(50):
            order_id = fake.md5()
            # 随机获取一个用户
            uid= random.randint(1, 3)
            username = fake.user_name()
            shopify_order_id = fake.md5()
            product_id = random.randint(1, 100)
            product_name = fake.name()
            variant_id = random.randint(1, 100)
            product_price = random.randint(1, 100)
            product_quantity = random.randint(1, 100)
            product_total_price = product_price * product_quantity
            product_type = random.randint(1, 3)
            order_status = random.randint(1, 5)
            pay_status = random.randint(1, 5)
            pay_time = fake.date_time().replace(tzinfo=timezone.utc)
            pay_amount = random.randint(1, 100)
            expired_at = timezone.now()+timezone.timedelta(days=random.randint(1, 100))
            proxy_num=product_quantity
            order=Orders.objects.create(order_id=order_id, uid=uid, username=username, shopify_order_id=shopify_order_id, product_id=product_id, product_name=product_name, variant_id=variant_id, product_price=product_price, product_quantity=product_quantity, product_total_price=product_total_price, product_type=product_type, order_status=order_status, pay_status=pay_status, pay_time=pay_time, pay_amount=pay_amount, expired_at=expired_at,proxy_num=proxy_num)

        status.update("[bold green]Done!")
if __name__ == '__main__':
    main()