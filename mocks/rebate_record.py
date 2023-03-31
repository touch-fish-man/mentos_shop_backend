import random
import string

from faker import Faker
import os
import sys
from init_env import *

from rich.console import Console

console = Console()

from apps.users.models import RebateRecord
from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating rebate records...") as status:
        RebateRecord.objects.all().delete()
        for i in range(100):
            uid = random.randint(1, 100)
            consumer_uid = random.randint(1, 100)
            reward_points = random.randint(1, 100)
            username = 'test'
            consumer_username = 'test'
            RebateRecord.objects.create(uid=uid, consumer_uid=consumer_uid, reward_points=reward_points, username=username, consumer_username=consumer_username)

if __name__ == '__main__':
    main()