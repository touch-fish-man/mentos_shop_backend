import random
import string

from faker import Faker

from init_env import *



from rich.console import Console
console = Console()

from apps.users.models import InviteLog
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating invite logs...") as status:
        InviteLog.objects.all().delete()
        for i in range(100):
            uid = random.randint(1, 100)
            inviter_uid = random.randint(1, 100)
            username = 'test'
            invite_code = ''.join(random.sample(string.ascii_letters + string.digits, 8))
            inviter_username = 'test'
            InviteLog.objects.create(uid=uid, inviter_uid=inviter_uid, invite_code=invite_code,
                                     username=username, inviter_username=inviter_username)

if __name__ == '__main__':
    main()