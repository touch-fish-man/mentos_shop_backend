import os
from init_env import *

from users import main as mock_users
from tickets import main as mock_tickets
from acls import main as mock_acls
from proxy import main as mock_proxy
from servers import main as mock_servers
from invite_log import main as mock_invite_log
from rebate_record import main as mock_rebate_record
from orders import main as mock_orders
from giftcard import main as mock_giftcard
from coupon_code import main as mock_coupon_code
from point_record import main as mock_point_record
from faq import main as mock_faq
from sync_shopify import main as sync_shopify
from product import main as mock_products
# 使用线程池，提高速度
from concurrent.futures import ThreadPoolExecutor,wait, ALL_COMPLETED
executor = ThreadPoolExecutor(10)
def main():
    mock_users()
    mock_orders()
    threads = []
    threads.append(executor.submit(mock_tickets))
    threads.append(executor.submit(mock_acls))
    threads.append(executor.submit(mock_servers))
    threads.append(executor.submit(mock_invite_log))
    threads.append(executor.submit(mock_rebate_record))
    # threads.append(executor.submit(mock_orders))
    threads.append(executor.submit(mock_giftcard))
    threads.append(executor.submit(mock_coupon_code))
    threads.append(executor.submit(mock_point_record))
    threads.append(executor.submit(mock_proxy))
    threads.append(executor.submit(mock_faq))
    threads.append(executor.submit(sync_shopify))

    wait(threads, return_when=ALL_COMPLETED)
    mock_products()
    print("mock data done")



if __name__ == '__main__':
    main()



