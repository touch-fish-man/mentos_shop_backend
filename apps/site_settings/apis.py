
from rest_framework.views import APIView
from pathlib import Path
import os
from apps.core.permissions import IsSuperUser

from apps.core.json_response import SuccessResponse,ErrorResponse
from apps.site_settings.services import save_site_settings,change_site_settings,get_site_setting

class SiteSettingsApi(APIView):
    """
    站点设置
    """
    permission_classes = [IsSuperUser]
    def post(self,request):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        save_site_settings(data=request.data,file=os.path.join(BASE_DIR, "config",".env"))
        revoke = change_site_settings()
        # 验证是否修改成功，失败则撤回修改
        if not revoke:
            data = get_site_setting()
            return SuccessResponse(msg="保存成功",data=data)
        else:
            save_site_settings(data=revoke,file=os.path.join(BASE_DIR, "config",".env"))
            return ErrorResponse(msg="保存失败",data={})
    
    def get(self,request):
        data = get_site_setting()
        return SuccessResponse(data=data,msg=("获取成功"))