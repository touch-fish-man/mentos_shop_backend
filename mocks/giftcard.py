import random
import string

from faker import Faker
import os
import sys

from init_env import *
from rich.console import Console

console = Console()

from apps.rewards.models import GiftCard
from django.utils import timezone
fake = Faker(locale='zh_CN')
discount_choices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1,"$1","$2","$3","$4","$5","$6","$7","$8","$9","$10"]

def main():
    with console.status("[bold green]Generating gift cards...") as status:
        GiftCard.objects.all().delete()
        for i in range(100):
            point = random.randint(1, 100)
            code = ''.join(random.sample(string.ascii_letters + string.digits, 8))
            mount = random.randint(1, 100)
            is_exchanged = random.choice([True, False])
            is_used = random.choice([True, False])
            uid = random.randint(1, 100)
            username = 'test'
            used_at = timezone.now()
            GiftCard.objects.create(point=point, code=code, mount=mount, is_exchanged=is_exchanged, is_used=is_used, uid=uid, username=username, used_at=used_at)

if __name__ == '__main__':
    main()