import os
from init_env import *

from users import create_default_user
from acls import create_acl_base 
from giftcard import main as mock_giftcard
from sync_shopify import main as sync_shopify
# 使用线程池，提高速度
from concurrent.futures import ThreadPoolExecutor,wait, ALL_COMPLETED
executor = ThreadPoolExecutor(15)
def main():
    clean_users()
    create_default_user()
    threads = []
    threads.append(executor.submit(create_acl_base))
    # threads.append(executor.submit(mock_invite_log))
    # threads.append(executor.submit(mock_rebate_record))
    # threads.append(executor.submit(mock_orders))
    threads.append(executor.submit(mock_giftcard))
    # threads.append(executor.submit(mock_coupon_code))
    # threads.append(executor.submit(mock_point_record))
    # threads.append(executor.submit(mock_faq))
    threads.append(executor.submit(sync_shopify))
    
    wait(threads, return_when=ALL_COMPLETED)
    # mock_products()
    # if not os.environ.get('DJANGO_ENV') == 'prod': # 生产环境不mock订单
    #     mock_orders()
    #     mock_proxy()
    
    print("mock data done")



if __name__ == '__main__':
    main()
