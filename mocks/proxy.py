import random
import string

from faker import Faker
import os
import sys
import time
from init_env import *
from rich.console import Console


console = Console()

from apps.proxy_server.models import Proxy,AclGroup
from apps.users.models import User
from apps.orders.models import Orders
from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating proxy servers...") as status:
        print("Generating proxy servers...")
        Proxy.objects.all().delete()
        order_count = Orders.objects.count()
        while order_count < 15:
            order_count = Orders.objects.count()
            time.sleep(10)
        for order in Orders.objects.all()[:10]:
            for i in range(50):
                print(i)
                ip = fake.ipv4()
                port = fake.port_number()
                user= random.choice(User.objects.all())
                username = fake.user_name()+str(random.randint(1, 100))
                password = fake.password()
                proxy_type = random.choice(['http', 'https', 'socks4', 'socks5'])
                server_id = random.randint(1, 100)
                acl_groups = random.sample(list(AclGroup.objects.all()), random.randint(1, 5))
                expired_at = timezone.now()+timezone.timedelta(days=random.randint(1, 100))
                proxy=Proxy.objects.create(ip=ip, port=port, username=username, password=password, proxy_type=proxy_type, server_id=server_id,expired_at=order.expired_at, user=user, order=order)
                proxy.acl_groups.set(acl_groups)


if __name__ == '__main__':
    main()