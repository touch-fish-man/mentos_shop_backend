from rest_framework.views import APIView
import os
from apps.core.permissions import IsSuperUser
from apps.core.permissions import IsAuthenticated
from apps.core.json_response import SuccessResponse,ErrorResponse
from apps.site_settings.services import save_site_settings,change_site_settings,get_site_setting
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings

class SiteSettingsApi(APIView, LoginRequiredMixin):
    """
    站点设置
    """
    permission_classes = [IsSuperUser]

    def post(self, request):
        BASE_DIR = settings.BASE_DIR
        if request.data.get("geofeed") is not None:
            os.makedirs("/opt/mentos_shop_backend/geofeed", exist_ok=True)
            with open("/opt/mentos_shop_backend/geofeed/geofeed.csv", "w") as f:
                f.write(request.data.get("geofeed"))
        save_site_settings(data=request.data, file=os.path.join(BASE_DIR, "config", ".env"))
        revoke = change_site_settings()
        # 验证是否修改成功，失败则撤回修改
        if not revoke:
            data = get_site_setting()
            return SuccessResponse(msg="保存成功", data=data)
        else:
            save_site_settings(data=revoke, file=os.path.join(BASE_DIR, "config", ".env"))
            return ErrorResponse(msg="保存失败", data={})

    def get(self, request):
        data = get_site_setting()
        try:
            geofeed = open("/opt/mentos_shop_backend/geofeed/geofeed.csv", "r").read()
        except:
            geofeed = ""
        data["geofeed"] = geofeed
        return SuccessResponse(data=data, msg=("获取成功"))
        
class SocialSettingsApi(APIView):
    def get(self, request):
        data = get_site_setting()
        ret_dict = {}
        ret_dict["discord"] = data.get("support_discord")
        ret_dict["twitter"] = data.get("support_twitter")
        return SuccessResponse(data=ret_dict, msg=("获取成功"))
class ServerLog(APIView):
    def get(self, request):
        BASE_DIR = settings.BASE_DIR
        # 获取日志
        if request.user.is_superuser:
            celery_logs = open(os.path.join(BASE_DIR, "logs", "celery_worker.log"), "r").read()
            django_logs = open(os.path.join(BASE_DIR, "logs", "server.log"), "r").read()
            celery_logs = celery_logs.split("\n")
            django_logs = django_logs.split("\n")
            celery_logs.reverse()
            django_logs.reverse()
            celery_logs = celery_logs[:200]
            django_logs = django_logs[:200]
            celery_logs= "\n".join(celery_logs)
            django_logs = "\n".join(django_logs)
            return SuccessResponse(data={"task_logs": celery_logs, "server_logs": django_logs}, msg=("获取成功"))