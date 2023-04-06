from celery import shared_task
from apps.celery import app
from apps.users.models import Code
from djcelery.models import PeriodicTask,CrontabSchedule
from datetime import timezone,timedelta
import json
import datetime
@app.task
def del_code(code_id):
    code = Code.objects.filter(id=code_id)
    code.delete()
@app.task
def del_emailcode(code_id):
    start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cron_objc=CrontabSchedule(
        minute=str(start_time.minute),
        hour=str(start_time.hour),
        day_of_month=str(start_time.day),
        month_of_year=str(start_time.month),
        year_of_month=str(start_time.year)
    )
    cron_objc.save()
    task_kwargs ={'code_id':code_id}
    task,create = PeriodicTask.objects.create(
        kwargs=json.dumps(task_kwargs),
        name='del_eamil',
        task='apps.users.task.del_code',
        cron_objc=cron_objc.id
    )
    task.save()
    if create:
        print("成功")
    else:
        print("失败")