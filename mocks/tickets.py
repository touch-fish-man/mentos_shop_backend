import random
import string

from django.contrib.auth.hashers import make_password
from faker import Faker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.production")

import django

django.setup()

from apps.tickets.models import Tickets

fake = Faker(locale='zh_CN')

def main():
    Tickets.objects.all().delete()
    for i in range(100):
        username = fake.name()
        email = fake.email()
        phone = fake.phone_number()
        message = fake.text()
        Tickets.objects.create(username=username, email=email, phone=phone, message=message)

if __name__ == '__main__':
    main()