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
    points = 1000
    level = 10
    invite_code = ''.join(random.sample(string.ascii_letters + string.digits, 6))
    User.objects.create(username=username, email=email, password=password, is_active=is_active,
                        is_superuser=is_superuser, points=points, level=level, invite_code=invite_code)


def clean_users():
    User.objects.all().delete()


def create_users():
    for i in range(100):
        username = fake.user_name()
        email = username.lower() + "@dafffa.site"
        is_superuser = random.choice([True, False])
        points = random.randint(0, 1000)
        level = random.randint(0, 10)
        invite_code = ''.join(random.sample(string.ascii_letters + string.digits, 6))
        password = make_password("Admin@123456")
        User.objects.create(username=username, email=email, password=password, is_active=True,
                            is_superuser=is_superuser, points=points, level=level, invite_code=invite_code)
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
