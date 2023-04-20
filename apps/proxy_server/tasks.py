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
        kaxy_client = KaxyClient(server.server_ip, server.server_port, server.server_username, server.server_password)
        if kaxy_client.check_server_status():
            server.server_status = 1
            server.faild_count = 0
        else:
            server.server_status = 0
            server.faild_count += 1
        server.save()
        if server.faild_count >= 5:
            # 服务器连续5次检查失败，给管理员发邮件
            pass