import random
import string

from faker import Faker
import os
import sys
import time
from init_env import *
from rich.console import Console


console = Console()

from apps.proxy_server.models import Proxy,ProxyStock

for xxx in ProxyStock.objects.all():
    if xxx.subnets:
        print(xxx.current_subnet)
        print(xxx.subnets.index(xxx.current_subnet))