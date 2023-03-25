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

from apps.users.models import RebateRecord
from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating rebate records...") as status:
        RebateRecord.objects.all().delete()
        for i in range(100):
            uid = random.randint(1, 100)
            consumer_uid = random.randint(1, 100)
            money = random.randint(1, 100)
            RebateRecord.objects.create(uid=uid, consumer_uid=consumer_uid, money=money)

if __name__ == '__main__':
    main()