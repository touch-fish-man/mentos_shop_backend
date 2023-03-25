import random
import string

from faker import Faker
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
import django

console = Console()
django.setup()

from apps.users.models import InviteLog
from django.utils import timezone
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating invite logs...") as status:
        InviteLog.objects.all().delete()
        for i in range(100):
            uid = random.randint(1, 100)
            inviter_uid = random.randint(1, 100)
            invite_code = ''.join(random.sample(string.ascii_letters + string.digits, 8))
            InviteLog.objects.create(uid=uid, inviter_uid=inviter_uid, invite_code=invite_code)

if __name__ == '__main__':
    main()