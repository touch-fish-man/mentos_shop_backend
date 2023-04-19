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
cidr_list=['217.144.59.0/24',
       '217.144.60.0/24',
       '213.181.216.0/24',
       '213.181.217.0/24',
       '213.181.218.0/24',
       '213.181.221.0/24',
       '113.203.224.0/24',
       '113.203.225.0/24',
       '113.203.223.0/24']
def main():
    with console.status("[bold green]Generating proxy servers...") as status:
        ServerGroup.objects.all().delete()
        Server.objects.all().delete()
        Cidr.objects.all().delete()
        print("Generating proxy servers...")
        for i in range(5):
            name = 'test proxy server {}'.format(i)
            description = fake.sentence()
            ip = '112.75.252.4'
            server = Server.objects.create(name=name, description=description, ip=ip)
            for cidr in cidr_list:
                ip_count = cidr_ip_count(cidr)
                cidr = Cidr.objects.create(cidr=cidr, ip_count=ip_count)
                server.cidrs.add(cidr)

        for i in range(10):
            name = 'test proxy server group {}'.format(i)
            description = fake.sentence()
            server_group = ServerGroup.objects.create(name=name, description=description)
            random_servers = Server.objects.order_by('?')[:random.randint(1, 3)]
            for server in random_servers:
                server_group.servers.add(server)

if __name__ == '__main__':
    main()