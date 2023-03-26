import os
if os.environ.get('DJANGO_ENV'):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(base_dir)
    if os.path.exists(os.path.join(base_dir, 'config', 'django', os.environ.get('DJANGO_ENV') + '.py')):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django." + os.environ.get('DJANGO_ENV'))
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.django.local")
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



