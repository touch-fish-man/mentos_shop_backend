import time
from datetime import datetime

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from apps.orders.services import create_proxy_by_id
from apps.proxy_server.models import Proxy
from celery import shared_task

from apps.utils.kaxy_handler import KaxyClient

@shared_task
def reset_proxy_fn(order_id, username, server_ip):
    ret_json = {}
    kaxy_client = KaxyClient(server_ip)
    kaxy_client.del_user(username)
    re_create_ret = create_proxy_by_id(order_id)
    if re_create_ret:
        delete_proxy_list=[]
        delete_proxy=Proxy.objects.filter(username=username).all()
        for p in delete_proxy:
            delete_proxy_list.append(p.ip)
            p.delete()
        ret_json['code'] = 200
        ret_json['message'] = '重置成功'
        ret_json['data'] = {}
        ret_json['data']['delete_proxy_list'] = delete_proxy_list
        ret_json['data']['order_id'] = order_id
        ret_json['data']['re_create'] = re_create_ret
        return ret_json
    else:
        ret_json['code'] = 500
        ret_json['message'] = '重置失败'
        ret_json['data'] = {}
        ret_json['data']['re_create'] = re_create_ret
        ret_json['data']['order_id'] = order_id
        return ret_json


def create_proxy_task(order_id, username, server_ip):
    # 创建一次性celery任务，立即执行，执行完毕后删除
    task_name = 'reset_proxy_{}_{}'.format(order_id, username)
    reset_proxy_fn.apply_async(args=[order_id, username, server_ip], task_id=task_name)