import random
import string

from faker import Faker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
import django

console = Console()
django.setup()

from apps.orders.models import Orders
from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating orders...") as status:
        Orders.objects.all().delete()
        for i in range(100):
            order_id = fake.md5()
            uid = random.randint(1, 100)
            username = fake.name()
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
            expired_at = fake.date_time().replace(tzinfo=timezone.utc)
            proxy_num = 4**random.randint(1, 5)
            Orders.objects.create(
                order_id=order_id,
                uid=uid,
                username=username,
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
            )
        status.update("[bold green]Done!")
