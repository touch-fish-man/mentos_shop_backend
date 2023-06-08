import datetime
import logging
import os
import threading

from django.utils import timezone

from apps.proxy_server.models import Server, ProxyStock
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
            resp = kaxy_client.get_server_info()
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
    logging.info("==========create_proxy_by_id {}==========".format(order_id))
    delete_proxy_list = []
    kaxy_client = KaxyClient(server_ip)
    kaxy_client.del_user(username)
    re_create_ret, ret_proxy_list,msg = create_proxy_by_id(order_id)
    if re_create_ret:
        new_proxy = Proxy.objects.filter(username=username).all()
        for p in new_proxy:
            if p.id not in ret_proxy_list and len(ret_proxy_list) > 0:
                p.delete()
        #创建库存回收任务
        from apps.tasks import celery_app
        # 更新产品库存
        celery_app.send_task('update_product_stock', name='重置代理回收库存')
        ret_json['code'] = 200
        ret_json['message'] = 'success'
        ret_json['data'] = {}
        ret_json['data']['delete_proxy_list'] = delete_proxy_list
        ret_json['data']['order_id'] = order_id
        ret_json['data']['re_create'] = re_create_ret
        logging.info("==========create_proxy_by_id success==========")
        return ret_json
    else:
        ret_json['code'] = 500
        ret_json['message'] = msg
        ret_json['data'] = {}
        ret_json['data']['re_create'] = re_create_ret
        ret_json['data']['order_id'] = order_id
        logging.info("==========create_proxy_by_id faild==========")
        return ret_json


@shared_task(name='delete_proxy_by_id')
def delete_proxy_by_id(id):
    pass


lock = threading.Lock()


@shared_task(name='delete_user_from_server')
def delete_user_from_server(server_ip, username, subnet, ip_stock_id):
    if Proxy.objects.filter(username=username).count() == 0:
        kax_client = KaxyClient(server_ip)
        kax_client.del_user(username)
        kax_client.del_acl(username)
        with lock:
            stock = ProxyStock.objects.filter(id=ip_stock_id).first()
            # 归还子网,归还库存
            if stock:
                if Proxy.objects.filter(subnet=subnet, ip_stock_id=stock.id).all().count() == 0:
                    stock.return_subnet(subnet)
                    stock.return_stock()
                    from apps.products.models import Variant
                    # 更新库存
                    variant = Variant.objects.filter(id=stock.variant_id).first()
                    if variant:
                        variant.save()


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
