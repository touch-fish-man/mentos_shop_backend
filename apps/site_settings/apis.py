from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from pathlib import Path
import os
from django.conf import settings

from apps.core.json_response import SuccessResponse
from apps.site_settings.services import save_site_settings,change_site_settings,get_site_setting

class SiteSettingsApi(APIView):
    def post(self,request):
        discord_cliend_id = int(request.data.get("discord_cliend_id"))
        discord_secret = request.data.get("discord_secret")
        discord_redirect_url = request.data.get("discord_redirect_url")
        discord_bind_redirect_url = request.data.get("discord_bind_redirect_url")
        
        api_key = request.data.get("api_key")
        api_scert = request.data.get("api_scert")
        app_password = request.data.get("app_password")
        shop_url = request.data.get("shop_url")

        email_method = request.data.get("email_method")
        email_code_expire = int(request.data.get("email_code_expire"))
        email_backend = request.data.get("email_backend")

        sendgrid_api_key = request.data.get("sendgrid_api_key")

        mailgun_api_key = request.data.get("mailgun_api_key")
        mailgun_sender_domain = request.data.get("mailgun_sender_domain")

        twitter = request.data.get("twitter")
        discord = request.data.get("discord")

        invite_level_points_per_user = int(request.data.get("invite_level_points_per_user"))
        billing_rate = float(request.data.get("billing_rate"))
        level_points_to_upgrade = int(request.data.get("level_points_to_upgrade"))
        level_points_decay_rate = float(request.data.get("level_points_decay_rate"))
        level_points_decay_day = int(request.data.get("level_points_decay_day"))
        min_level = int(request.data.get("min_level"))
        max_level = int(request.data.get("max_level"))
        level_discount_rate = float(request.data.get("level_discount_rate"))

        invite_rebate_rate = float(request.data.get("invite_rebate_rate"))

        settings_var = ['DISCORD_CLIENT_ID','DISCORD_CLIENT_SECRET','DISCORD_REDIRECT_URI',
                   'DISCORD_BIND_REDIRECT_URI','SHOPIFY_API_KEY','SHOPIFY_API_SECRET','SHOPIFY_APP_KEY',
                   'SHOPIFY_SHOP_URL','EMAIL_METHOD','EMAIL_CODE_EXPIRE','EMAIL_BACKEND','SENDGRID_API_KEY',
                   'MAILGUN_API_KEY','MAILGUN_SENDER_DOMAIN','SUPPORT_TWITTER','SUPPORT_DISCORD',
                   'INVITE_LEVEL_POINTS_PER_USER','BILLING_RATE','LEVEL_POINTS_TO_UPGRADE','LEVEL_POINTS_DECAY_RATE',
                   'LEVEL_POINTS_DECAY_DAY','MIN_LEVEL','MAX_LEVEL','LEVEL_DISCOUNT_RATE','INVITE_REBATE_RATE']
        
        new_value = [discord_cliend_id,discord_secret,discord_redirect_url,
                   discord_bind_redirect_url,api_key,api_scert,app_password,
                   shop_url,email_method,email_code_expire,email_backend,sendgrid_api_key,
                   mailgun_api_key,mailgun_sender_domain,twitter,discord,
                   invite_level_points_per_user,billing_rate,level_points_to_upgrade,
                    level_points_decay_rate,level_points_decay_day,min_level, max_level,
                     level_discount_rate,invite_rebate_rate ]


        change_site_settings(request=request)
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        save_site_settings(os.path.join(BASE_DIR, "config\.env"),settings_var,new_value)
        return SuccessResponse(msg="保存成功")
    
    def get(self,request):
        data = get_site_setting()
        return SuccessResponse(data=data,msg=("获取成功"))