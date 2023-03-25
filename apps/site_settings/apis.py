from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from pathlib import Path
import os
from django.conf import settings

from apps.core.json_response import SuccessResponse
from apps.site_settings.services import save_site_settings

class SiteSettingsApi(APIView):
    def post(self,request):
        discord_cliend_id = request.data.get("discord_cliend_id")
        discord_secret = request.data.get("discord_secret")
        discord_redirect_url = request.data.get("discord_redirect_url")
        discord_bind_redirect_url = request.data.get("discord_bind_redirect_url")
        
        api_key = request.data.get("api_key")
        api_scert = request.data.get("api_scert")
        app_password = request.data.get("app_password")
        shop_url = request.data.get("shop_url")


        twitter = request.data.get("twitter")
        discord = request.data.get("discord")

        settings_var = ['DISCORD_CLIENT_ID','DISCORD_CLIENT_SECRET','DISCORD_REDIRECT_URI',
                   'DISCORD_BIND_REDIRECT_URI','SHOPIFY_API_KEY','SHOPIFY_API_SECRET','SHOPIFY_APP_KEY',
                   'SHOPIFY_SHOP_URL','SUPPORT_TWITTER','SUPPORT_DISCORD']
        new_value = [discord_cliend_id,discord_secret,discord_redirect_url,
                   discord_bind_redirect_url,api_key,api_scert,app_password,
                   shop_url,twitter,discord]

        # settings_var = ['EMAIL_PORT','EMAIL_FROM']
        # new_value = [email_port,email_from]

        settings.DISCORD_CLIENT_ID = discord_cliend_id
        settings.DISCORD_CLIENT_SECRET = discord_secret
        settings.DISCORD_REDIRECT_URI = discord_redirect_url
        settings.DISCORD_BIND_REDIRECT_URI = discord_bind_redirect_url
        
        settings.SHOPIFY_API_KEY = api_key
        settings.SHOPIFY_API_SECRET = api_scert
        settings.SHOPIFY_APP_KEY = app_password
        settings.SHOPIFY_SHOP_URL = shop_url

        settings.SUPPORT_TWITTER = twitter
        settings.SUPPORT_DISCORD = discord

        # site = Site_Settings.objects.create(discord_cliend_id=discord_cliend_id,discord_secret=discord_secret,
        #                                     discord_redirect_url=discord_redirect_url,discord_bind_redirect_url=discord_bind_redirect_url,
        #                                     api_key=api_key,api_scert=api_scert,app_password=app_password,shop_url=shop_url,
        #                                     twitter=twitter,discord=discord)
        # site.save()

        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        save_site_settings(os.path.join(BASE_DIR, "config\.env"),settings_var,new_value)
        return SuccessResponse(msg="保存成功")
