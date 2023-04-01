import random
import string

from faker import Faker
import os
import sys

from init_env import *

from apps.proxy_server.models import Acls,AclGroup
from rich.console import Console

console = Console()
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating proxy servers...") as status:
        AclGroup.objects.all().delete()
        Acls.objects.all().delete()
        for i in range(50):
            name = 'test acl rule {}'.format(i)
            description = fake.sentence()
            acl_value = []
            for i in range(10):
                acl_value.append(fake.domain_name())
            acl_value='\n'.join(acl_value)
            Acls.objects.create(name=name, description=description, acl_value=acl_value)
        for i in range(10):
            name = 'test acl group {}'.format(i)
            description = fake.sentence()
            acl_group=AclGroup.objects.create(name=name, description=description)
            random_acls = Acls.objects.order_by('?')[:random.randint(1, 10)]
            for acl in random_acls:
                acl_group.acls.add(acl)



if __name__ == '__main__':
    main()