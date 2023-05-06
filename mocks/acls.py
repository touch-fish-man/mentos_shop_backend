import random
import string
from pprint import pprint

from faker import Faker
import os
import sys
from init_env import *

from apps.proxy_server.models import Acls,AclGroup
from rich.console import Console

console = Console()
fake = Faker(locale='zh_CN')

# 按列读取csv文件,返回一个字典,字典的key为csv文件的第一行,字典的value为对应的列每行的值组成的list 并且去掉了空行，去重
def read_csv(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
        keys = lines[0].strip().split(',')
        values = [line.strip().split(',') for line in lines[1:]]
        return {key: list(set(value[i] for value in values if value[i])) for i, key in enumerate(keys)}
def create_acl_base():
    for data_key, data_value in data.items():
                acl_value="\n".join(data_value)
                description = fake.sentence()
                Acls.objects.create(name=data_key, acl_value=acl_value, description=description)
def main():
    base__dir = os.path.dirname(os.path.abspath(__file__))
    data = read_csv(os.path.join(base__dir, 'acl_list.csv'))
    with console.status("[bold green]Generating acl...") as status:
        print("Generating acl...")
        AclGroup.objects.all().delete()
        Acls.objects.all().delete()
        create_acl_base()
        for i in range(5):
            name = 'test acl group {}'.format(i)
            description = fake.sentence()
            acl_group=AclGroup.objects.create(name=name, description=description)
            random_acls = random.sample(list(Acls.objects.all()), 3)
            acl_group.name = '+'.join([acl.name for acl in random_acls])
            acl_group.acls.set(random_acls)
            acl_value=[]
            for acl in random_acls:
                acl_value.extend(acl.acl_value.split('\n'))
            acl_value=list(set(acl_value))
            acl_value.sort()
            acl_group.acl_value='\n'.join(acl_value)
            acl_group.save()
        print("Done!")




if __name__ == '__main__':
    main()