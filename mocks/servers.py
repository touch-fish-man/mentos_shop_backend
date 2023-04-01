import random
import string

from faker import Faker
import os
import sys

from init_env import *

from apps.proxy_server.models import Server,ServerGroup
from rich.console import Console

console = Console()

fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating proxy servers...") as status:
        ServerGroup.objects.all().delete()
        for i in range(50):
            name = 'test proxy server group {}'.format(i)
            description = fake.sentence()
            ServerGroup.objects.create(name=name, description=description)
        Server.objects.all().delete()
        for i in range(50):
            name = 'test proxy server {}'.format(i)
            description = fake.sentence()
            ip = fake.ipv4()
            cidr_prefix = ",".join([fake.ipv4(network=True) for i in range(4)])
            server=Server.objects.create(name=name, description=description, ip=ip, cidr_prefix=cidr_prefix)
            server.server_groups.add(random.choice(ServerGroup.objects.all()))
if __name__ == '__main__':
    main()