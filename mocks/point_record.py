from init_env import *
from rich.console import Console
import random
import string

from faker import Faker
import os
import sys
console = Console()

from apps.rewards.models import PointRecord
from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating coupon codes...") as status:
        PointRecord.objects.all().delete()
        for i in range(50):
            uid = random.randint(1,3)
            username = 'test'
            point = random.randint(-100, 100)
            reason = random.choice(['签到', '邀请好友', '兑换礼品卡'])
            PointRecord.objects.create(uid=uid, username=username, point=point, reason=reason)

if __name__ == '__main__':
    main()