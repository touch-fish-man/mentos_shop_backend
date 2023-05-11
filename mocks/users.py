# 批量创建用户

import random
import string
import uuid
from init_env import *
from django.contrib.auth.hashers import make_password
from faker import Faker
import os
import sys

from rich.console import Console


from apps.users.models import User

fake = Faker(locale='en_US')


def create_default_user():
    username = "admin"
    email = "admin@admin.com"
    password = make_password("Admin@123456")
    is_superuser = True
    is_active = True
    level_points = 10000
    level = 5
    reward_points = 110000
    invite_count = 100
    discord_id = 758212164619075614
    discord_name = fake.user_name()
    if not User.objects.filter(username=username).exists():
        User.objects.create(username=username, email=email, password=password, is_active=is_active,
                        is_superuser=is_superuser, level_points=level_points, level=level, reward_points=reward_points,invite_count=invite_count,discord_id=discord_id,discord_name=discord_name)
    username = "test"
    email = "test@test.com"
    password = make_password("Admin@123456")
    is_superuser = False
    is_active = True
    level_points = 10000
    level = 5
    reward_points = 110000
    invite_count = 100
    if not User.objects.filter(username=username).exists():
        User.objects.create(username=username, email=email, password=password, is_active=is_active,
                        is_superuser=is_superuser, level_points=level_points, level=level, reward_points=reward_points,invite_count=invite_count)


def clean_users():
    User.objects.all().delete()

def make_user():
    user_dict= {}
    username = fake.user_name()
    email = username.lower() + "@dafffa.site"
    is_superuser = random.choice([True, False])
    level = random.randint(1, 5)
    password = make_password("Admin@123456")
    level_points = random.randint(0, 1000)
    reward_points = random.randint(0, 1000)
    invite_count = random.randint(0, 100)
    discord_id = str(uuid.uuid4())[:16]
    discord_name = fake.user_name()
    user_dict['username'] = username
    user_dict['email'] = email
    user_dict['is_superuser'] = is_superuser
    user_dict['level'] = level
    user_dict['password'] = password
    user_dict['level_points'] = level_points
    user_dict['reward_points'] = reward_points
    user_dict['invite_count'] = invite_count
    # user_dict['discord_id'] = discord_id
    # user_dict['discord_name'] = discord_name
    return user_dict


def create_users():
    for i in range(30):
        while True:
            user_dict = make_user()
            # if User.objects.filter(username=user_dict['username']).exists():
            #     continue
            if User.objects.filter(email=user_dict['email']).exists():
                continue
            # if User.objects.filter(discord_id=user_dict['discord_id']).exists():
            #     continue
            User.objects.create(**user_dict)
            break

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
