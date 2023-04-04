import random
import string

from faker import Faker
import os
import sys

from init_env import *
from rich.console import Console

console = Console()

from apps.rewards.models import GiftCard,LevelCode
from django.utils import timezone
fake = Faker(locale='zh_CN')
discount_choices = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1,"$1","$2","$3","$4","$5","$6","$7","$8","$9","$10"]
level_choices = [0,0.1,0.2,0.3,0.4]
level_points = [0,1000,2000,3000,4000]

def main():
    with console.status("[bold green]Generating gift cards...") as status:
        print("Generating gift cards...")
        GiftCard.objects.all().delete()
        for i in range(50):
            point = random.randint(1, 100)
            code = ''.join(random.sample(string.ascii_letters + string.digits, 8))
            mount = random.randint(1, 100)
            is_exchanged = random.choice([True, False])
            GiftCard.objects.create(point=point, code=code, mount=mount, is_exchanged=is_exchanged)
        LevelCode.objects.all().delete()
        for i in range(5):
            discount = level_choices[i]
            code = ''.join(random.sample(string.ascii_letters + string.digits, 8))
            level_point=level_points[i]
            level=i+1
            LevelCode.objects.create(discount=discount, code=code,point=level_point,level=level)

if __name__ == '__main__':
    main()