import random
import string

from faker import Faker
import os
import sys
import time
from init_env import *
from rich.console import Console


console = Console()

from apps.proxy_server.models import Proxy,AclGroup,Server
from apps.users.models import User
from apps.orders.models import Orders

from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating proxy servers...") as status:
        print("Generating proxy servers...")
        Proxy.objects.all().delete()
        for order in Orders.objects.all()[:5]:
            for i in range(50):
                ip = fake.ipv4()
                port = fake.port_number()
                user= random.choice(User.objects.all())
                username = fake.user_name()+str(random.randint(1, 100))
                password = fake.password()
                proxy_type = "http"
                server_ip = random.choice(Server.objects.all()).ip
                proxy=Proxy.objects.create(ip=ip, port=port, username=username, password=password, proxy_type=proxy_type, server_ip=server_ip,expired_at=order.expired_at, user=user, order=order)

if __name__ == '__main__':
    main()