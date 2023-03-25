# 批量创建用户

import random
import string

from django.contrib.auth.hashers import make_password
from faker import Faker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rich.console import Console
import django

django.setup()

from apps.users.models import User

fake = Faker(locale='en_US')


def create_default_user():
    username = "admin"
    email = "admin@admin.com"
    password = make_password("Admin@123456")
    is_superuser = True
    is_active = True
    level_points = 1000
    level = 5
    reward_points = 1000
    invite_count = 100
    User.objects.create(username=username, email=email, password=password, is_active=is_active,
                        is_superuser=is_superuser, level_points=level_points, level=level, reward_points=reward_points,invite_count=invite_count)


def clean_users():
    User.objects.all().delete()


def create_users():
    for i in range(100):
        username = fake.user_name()
        email = username.lower() + "@dafffa.site"
        is_superuser = random.choice([True, False])
        level = random.randint(1, 5)
        password = make_password("Admin@123456")
        level_points = random.randint(0, 1000)
        reward_points = random.randint(0, 1000)
        invite_count = random.randint(0, 100)

        User.objects.create(username=username, email=email, password=password, is_active=True,
                            is_superuser=is_superuser, level_points=level_points, level=level, reward_points=reward_points,invite_count=invite_count)
def main():
    console = Console()
    with console.status("[bold green]Generating users...") as status:
        clean_users()
        create_default_user()
        create_users()


if __name__ == '__main__':
    clean_users()
    create_default_user()
    create_users()
