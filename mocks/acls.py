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
        for i in range(50):
            name = 'test acl group {}'.format(i)
            description = fake.sentence()
            AclGroup.objects.create(name=name, description=description)
        Acls.objects.all().delete()
        for i in range(50):
            name = 'test acl rule {}'.format(i)
            description = fake.sentence()
            acl_value = []
            for i in range(10):
                acl_value.append(fake.domain_name())

            acl_value='\n'.join(acl_value)
            acl=Acls.objects.create(name=name, description=description, acl_value=acl_value)
            acl.acl_groups.add(random.choice(AclGroup.objects.all()))


if __name__ == '__main__':
    main()