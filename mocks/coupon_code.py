import random
import string

from faker import Faker
import os
import sys

from init_env import *
from rich.console import Console

console = Console()

from apps.rewards.models import CouponCode
from django.utils import timezone
fake = Faker(locale='zh_CN')
discount_choices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1,"$1","$2","$3","$4","$5","$6","$7","$8","$9","$10"]

def main():
    with console.status("[bold green]Generating coupon codes...") as status:
        CouponCode.objects.all().delete()
        for i in range(100):
            code = ''.join(random.sample(string.ascii_letters + string.digits, 8))
            discount = random.choice(discount_choices)
            code_type = random.choice([1, 2])
            is_used = random.choice([True, False])
            used_at = timezone.now()
            holder_uid = random.randint(1, 100)
            holder_username = 'test'
            CouponCode.objects.create(code=code, discount=discount, code_type=code_type, is_used=is_used, used_at=used_at, holder_uid=holder_uid, holder_username=holder_username)

if __name__ == '__main__':
    main()