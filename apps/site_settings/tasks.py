import datetime

from drf_api_logger.models import APILogsModel
from celery import shared_task


@shared_task(name='delete_api_logs')
def delete_api_logs():
    """
    删除api日志
    """
    delete_list=APILogsModel.objects.filter(added_on__lt=datetime.datetime.now() - datetime.timedelta(days=2)).all()
    for d in delete_list:
        d.delete()
    return {'message': 'delete {} api logs done '.format(str(len(delete_list)))}
