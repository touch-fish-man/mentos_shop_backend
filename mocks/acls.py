import random
import string

from faker import Faker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.production")

import django

django.setup()

from apps.proxy_server.models import AclList

fake = Faker(locale='zh_CN')

def main():
    AclList.objects.all().delete()
    for i in range(100):
        name = 'test acl rule {}'.format(i)
        description = fake.sentence()
        acl_value = []
        for i in range(10):
            acl_value.append(fake.domain_name())

        acl_value='\n'.join(acl_value)
        AclList.objects.create(name=name, description=description, acl_value=acl_value)

if __name__ == '__main__':
    main()