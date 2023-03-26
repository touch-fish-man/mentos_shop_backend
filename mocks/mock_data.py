import os
if os.environ.get('DJANGO_ENV') == 'prod':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.production")
elif os.environ.get('DJANGO_ENV') == 'local':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
elif os.environ.get('DJANGO_ENV') == 'test':
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.test")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")

from users import main as mock_users
from tickets import main as mock_tickets
from acls import main as mock_acls
from proxy import main as mock_proxy
from servers import main as mock_servers
from invite_log import main as mock_invite_log
from rebate_record import main as mock_rebate_record
from orders import main as mock_orders
# 使用线程池，提高速度
from concurrent.futures import ThreadPoolExecutor,wait, ALL_COMPLETED
executor = ThreadPoolExecutor(10)
def main():
    threads = []
    threads.append(executor.submit(mock_users))
    threads.append(executor.submit(mock_tickets))
    threads.append(executor.submit(mock_acls))
    threads.append(executor.submit(mock_proxy))
    threads.append(executor.submit(mock_servers))
    threads.append(executor.submit(mock_invite_log))
    threads.append(executor.submit(mock_rebate_record))
    threads.append(executor.submit(mock_orders))
    wait(threads, return_when=ALL_COMPLETED)
    print("mock data done")



if __name__ == '__main__':
    main()



