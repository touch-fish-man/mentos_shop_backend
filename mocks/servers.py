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
        Cidr.objects.all().delete()
        print("Generating proxy servers...")
        for i in range(10):
            name = 'test proxy server {}'.format(i)
            description = fake.sentence()
            ip = '112.75.252.4'
            server = Server.objects.create(name=name, description=description, ip=ip)
            cidr = fake.ipv4(network=True)
            while int(cidr.split('/')[1])>29:
                cidr = fake.ipv4(network=True)
            if int(cidr.split('/')[1])<25:
                cidr = cidr.split('/')[0]+'/'+str(random.randint(25, 29))
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