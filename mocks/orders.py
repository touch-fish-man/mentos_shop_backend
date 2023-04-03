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
        Orders.objects.all().delete()
        for i in range(50):
            order_id = fake.md5()
            # 随机获取一个用户
            uid= random.randint(1, 100)
            username = fake.user_name()
            shopify_order_id = fake.md5()
            product_id = random.randint(1, 100)
            product_name = fake.name()
            product_price = random.randint(1, 100)
            product_num = random.randint(1, 100)
            product_total_price = product_price * product_num
            product_type = random.randint(1, 100)
            pay_url = fake.url()
            order_status = random.randint(1, 5)
            pay_type = random.randint(1, 5)
            pay_status = random.randint(1, 5)
            pay_time = fake.date_time().replace(tzinfo=timezone.utc)
            pay_amount = random.randint(1, 100)
            pay_no = fake.md5()
            pay_remark = fake.text()
            pay_callback_time = fake.date_time().replace(tzinfo=timezone.utc)
            pay_callback_status = random.randint(1, 5)
            expired_at = fake.future_datetime().replace(tzinfo=timezone.utc)
            proxy_num = 4**random.randint(1, 5)
            order=Orders.objects.create(
                order_id=order_id,
                shopify_order_id=shopify_order_id,
                product_id=product_id,
                product_name=product_name,
                product_price=product_price,
                product_num=product_num,
                product_total_price=product_total_price,
                product_type=product_type,
                pay_url=pay_url,
                order_status=order_status,
                pay_type=pay_type,
                pay_status=pay_status,
                pay_time=pay_time,
                pay_amount=pay_amount,
                pay_no=pay_no,
                pay_remark=pay_remark,
                pay_callback_time=pay_callback_time,
                pay_callback_status=pay_callback_status,
                expired_at=expired_at,
                proxy_num=proxy_num,
                uid=uid,
                username=username
            )

        status.update("[bold green]Done!")
if __name__ == '__main__':
    main()