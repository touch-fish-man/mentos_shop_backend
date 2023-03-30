import random
import string

from faker import Faker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django

django.setup()

from apps.proxy_server.models import Server
from rich.console import Console

console = Console()

fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating proxy servers...") as status:
        Server.objects.all().delete()
        for i in range(100):
            name = 'test proxy server {}'.format(i)
            description = fake.sentence()
            ip = fake.ipv4()
            cidr_prefix = ",".join([fake.ipv4(network=True) for i in range(4)])
            Server.objects.create(name=name, description=description, ip=ip, cidr_prefix=cidr_prefix)
if __name__ == '__main__':
    main()