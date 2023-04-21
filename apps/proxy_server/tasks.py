from celery import shared_task
from apps.proxy_server.models import Server
from apps.utils.kaxy_handler import KaxyClient


@shared_task(name='check_server_status')
def check_server_status():
    """
    检查服务器状态,每10分钟检查一次
    """
    servers = Server.objects.filter().all()
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
            # 服务器连续5次检查失败，给管理员发邮件
            pass