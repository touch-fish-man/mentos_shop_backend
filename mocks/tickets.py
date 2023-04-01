import random
import string

from faker import Faker
import os
import sys

from init_env import *
from rich.console import Console


from apps.tickets.models import Tickets

fake = Faker(locale='zh_CN')

def main():
    console = Console()
    with console.status("[bold green]Generating tickets...") as status:
        Tickets.objects.all().delete()
        for i in range(50):
            username = fake.name()
            email = fake.email()
            phone = fake.phone_number()
            message = fake.text()
            Tickets.objects.create(username=username, email=email, phone=phone, message=message)

if __name__ == '__main__':
    main()