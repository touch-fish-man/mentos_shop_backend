import random
import string

from faker import Faker
import os
import sys

from init_env import *
from rich.console import Console


console = Console()

from apps.proxy_server.models import ProxyList
from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating proxy servers...") as status:
        ProxyList.objects.all().delete()
        for i in range(50):
            ip = fake.ipv4()
            port = fake.port_number()
            username = fake.user_name()+str(random.randint(1, 100))
            password = fake.password()
            proxy_type = random.choice(['http', 'https', 'socks4', 'socks5'])
            server_id = random.randint(1, 100)
            acl_ids = ",".join([str(random.randint(1, 100)) for i in range(4)])
            order_id = random.randint(1, 100)
            uid = random.randint(1, 100)
            expired_at = timezone.now()+timezone.timedelta(days=random.randint(1, 100))
            ProxyList.objects.create(ip=ip, port=port, username=username, password=password, proxy_type=proxy_type, server_id=server_id, acl_ids=acl_ids, order_id=order_id, uid=uid, expired_at=expired_at)


if __name__ == '__main__':
    main()