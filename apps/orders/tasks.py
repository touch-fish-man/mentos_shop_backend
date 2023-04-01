# from celery import shared_task
from apps.celery import app
from datetime import timedelta
from apps.orders.models import Orders
from apps.users.models import User
from django.utils import timezone
# @shared_task
@app.task()
def add(a,b):
    print("10秒到了啊啊啊啊啊啊啊。。。。。。。。。。。。")
    return a+b
    # all_expire_order = Orders.objects.filter()
    