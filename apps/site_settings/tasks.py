import datetime

from drf_api_logger.models import APILogsModel
from celery import shared_task


@shared_task(name='delete_api_logs')
def delete_api_logs():
    """
    删除api日志
    """
    APILogsModel.objects.filter(created_at__lt=datetime.datetime.now() - datetime.timedelta(days=3)).delete()
    print('delete_api_logs done at %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

