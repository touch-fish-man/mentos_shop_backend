import datetime
import logging

from django.utils import timezone

from apps.proxy_server.models import Server
import json
import time

from django_celery_beat.models import PeriodicTask, IntervalSchedule

from apps.orders.services import create_proxy_by_id
from apps.proxy_server.models import Proxy
from celery import shared_task

from apps.utils.kaxy_handler import KaxyClient

@shared_task(name='check_server_status')
def check_server_status():
    """
    检查服务器状态,每10分钟检查一次
    """
    servers = Server.objects.filter(faild_count__lt=5).all()
    for server in servers:
        kaxy_client = KaxyClient(server.ip)
        try:
            resp=kaxy_client.get_server_info()
            if resp.status_code == 200:
                server.server_status = 1
                server.faild_count = 0
            else:
                server.server_status = 0
                server.faild_count += 1
        except Exception as e:
            server.server_status = 0
            server.faild_count += 1
        server.save()
        if server.faild_count >= 5:
            # 服务器连续5次检查失败
            pass
    print('check_server_status done at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@shared_task(name='reset_proxy')
def reset_proxy_fn(order_id, username, server_ip):
    ret_json = {}
    logging.info("==========create_proxy_by_id==========")
    delete_proxy = Proxy.objects.filter(username=username).all()
    delete_proxy_list = []
    kaxy_client = KaxyClient(server_ip)
    kaxy_client.del_user(username)
    re_create_ret = create_proxy_by_id(order_id)
    if re_create_ret:
        new_proxy_cnt = Proxy.objects.filter(username=username).count()
        if new_proxy_cnt>len(delete_proxy):
            for de in delete_proxy:
                delete_proxy_list.append(de.ip)
                de.delete()
        ret_json['code'] = 200
        ret_json['message'] = '重置成功'
        ret_json['data'] = {}
        ret_json['data']['delete_proxy_list'] = delete_proxy_list
        ret_json['data']['order_id'] = order_id
        ret_json['data']['re_create'] = re_create_ret
        logging.info("==========create_proxy_by_id success==========")
        return ret_json
    else:
        ret_json['code'] = 500
        ret_json['message'] = '重置失败'
        ret_json['data'] = {}
        ret_json['data']['re_create'] = re_create_ret
        ret_json['data']['order_id'] = order_id
        logging.info("==========create_proxy_by_id faild==========")
        return ret_json

def create_proxy_task(order_id, username, server_ip):
    # 创建一次性celery任务，立即执行，执行完毕后删除
    interval = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.SECONDS)[0]
    # 删除已有且已过期的任务
    PeriodicTask.objects.filter(name=f'重置代理_{order_id}', one_off=True, expires__lte=timezone.now()).delete()

    PeriodicTask.objects.get_or_create(
        name=f'重置代理_{order_id}',
        task='reset_proxy',
        args=json.dumps([order_id, username, server_ip]),
        interval=interval,
        one_off=True,
        expires=timezone.now() + datetime.timedelta(seconds=70)
    )
