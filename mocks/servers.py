import random
import string

from faker import Faker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.production")

import django

django.setup()

from apps.proxy_server.models import ProxyServer

fake = Faker(locale='zh_CN')

def main():
    ProxyServer.objects.all().delete()
    for i in range(100):
        name = 'test proxy server {}'.format(i)
        description = fake.sentence()
        ip = fake.ipv4()
        cidr_prefix = ",".join([fake.ipv4(network=True) for i in range(4)])
        ProxyServer.objects.create(name=name, description=description, ip=ip, cidr_prefix=cidr_prefix)
if __name__ == '__main__':
    main()