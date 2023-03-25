from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from pathlib import Path
import os
from django.conf import settings
from apps.site_settings.models import Site_Settings
from apps.core.json_respon import JsonResponse
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

        email_port = request.data.get("email_port")
        email_from = request.data.get("email_from")

        twitter = request.data.get("twitter")
        discord = request.data.get("discord")

        settings_var = ['DISCORD_CLIENT_ID','DISCORD_CLIENT_SECRET','DISCORD_REDIRECT_URI',
                   'DISCORD_BIND_REDIRECT_URI','API_KEY','API_SCERT','APP_PASSWORD',
                   'SHOP_URL','EMAIL_PORT','EMAIL_FROM','TWITTER','DISCORD']
        new_value = [discord_cliend_id,discord_secret,discord_redirect_url,
                   discord_bind_redirect_url,api_key,api_scert,app_password,
                   shop_url,email_port,email_from,twitter,discord]

        # settings_var = ['EMAIL_PORT','EMAIL_FROM']
        # new_value = [email_port,email_from]

        settings.DISCORD_CLIENT_ID = discord_cliend_id
        settings.DISCORD_CLIENT_SECRET = discord_secret
        settings.DISCORD_REDIRECT_URI = discord_redirect_url
        settings.DISCORD_BIND_REDIRECT_URI = discord_bind_redirect_url
        
        settings.API_KEY = api_key
        settings.API_SCERT = api_scert
        settings.APP_PASSWORD = app_password
        settings.SHOP_URL = shop_url

        settings.EMAIL_PORT = email_port
        settings.EMAIL_FROM = email_from

        settings.TWITTER = twitter
        settings.DISCORD = discord

        # site = Site_Settings.objects.create(discord_cliend_id=discord_cliend_id,discord_secret=discord_secret,
        #                                     discord_redirect_url=discord_redirect_url,discord_bind_redirect_url=discord_bind_redirect_url,
        #                                     api_key=api_key,api_scert=api_scert,app_password=app_password,shop_url=shop_url,
        #                                     twitter=twitter,discord=discord)
        # site.save()

        BASE_DIR = Path(__file__).resolve().parent.parent.parent

        save_site_settings(os.path.join(BASE_DIR, "config\.env"),settings_var,new_value)
        return JsonResponse(msg="保存成功")
