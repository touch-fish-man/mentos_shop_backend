from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from pathlib import Path
import os


from apps.core.json_response import SuccessResponse
from apps.site_settings.services import save_site_settings,change_site_settings,get_site_setting

class SiteSettingsApi(APIView):
    """
    站点设置
    """
    def post(self,request):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        save_site_settings(request=request,file=os.path.join(BASE_DIR, "config",".env"))
        change_site_settings()
        data = get_site_setting()
        return SuccessResponse(msg="保存成功",data=data)
    
    def get(self,request):
        data = get_site_setting()
        return SuccessResponse(data=data,msg=("获取成功"))