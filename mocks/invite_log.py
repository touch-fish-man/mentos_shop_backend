import random
import string

from faker import Faker

from init_env import *



from rich.console import Console
console = Console()

from apps.users.models import InviteLog, User
fake = Faker(locale='zh_CN')

def main():
    with console.status("[bold green]Generating invite logs...") as status:
        print("Generating invite logs...")
        InviteLog.objects.all().delete()
        for i in range(50):
            uid = random.randint(1, 10)
            inviter_uid = random.randint(1, 10)
            username = 'test'
            invite_code = ''.join(random.sample(string.ascii_letters + string.digits, 8))
            inviter_username = 'test'
            user = random.choice(User.objects.all())
            inviter_user= random.choice(User.objects.all())
            InviteLog.objects.create(uid=uid, inviter_uid=inviter_uid, invite_code=invite_code,
                                     username=username, inviter_username=inviter_username, user=user, inviter_user=inviter_user)

if __name__ == '__main__':
    main()