import random
import string

from faker import Faker
import os
import sys

from init_env import *

from apps.proxy_server.models import Server, ServerGroup, Cidr, cidr_ip_count
from rich.console import Console

console = Console()

fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating proxy servers...") as status:
        ServerGroup.objects.all().delete()
        Server.objects.all().delete()
        print("Generating proxy servers...")
        for i in range(50):
            name = 'test proxy server {}'.format(i)
            description = fake.sentence()
            ip = fake.ipv4()
            cidr = fake.ipv4(network=True)
            ip_count = cidr_ip_count(cidr)
            cidr = Cidr.objects.create(cidr=cidr, ip_count=ip_count)
            server = Server.objects.create(name=name, description=description, ip=ip)
            server.cidrs.add(cidr)
            cidr = fake.ipv4(network=True)
            ip_count = cidr_ip_count(cidr)
            cidr = Cidr.objects.create(cidr=cidr, ip_count=ip_count)
            server.cidrs.add(cidr)

        for i in range(10):
            name = 'test proxy server group {}'.format(i)
            description = fake.sentence()
            server_group = ServerGroup.objects.create(name=name, description=description)
            random_servers = Server.objects.order_by('?')[:random.randint(1, 10)]
            for server in random_servers:
                server_group.servers.add(server)

if __name__ == '__main__':
    main()