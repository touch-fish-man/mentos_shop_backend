import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from captcha.views import CaptchaStore
import pytz
from datetime import datetime, timedelta

def exchange_code(code: str, redirect_uri):
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "scope": "identify"
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    credentials = response.json()
    access_token = credentials['access_token']
    # refresh_token = credentials['refresh_token']
    response = requests.get("https://discord.com/api/v6/users/@me", headers={
        'Authorization': 'Bearer %s' % access_token
    })
    user = response.json()
    return user
# def refresh_token(refresh_token):
#     data = {
#         "client_id": settings.DISCORD_CLIENT_ID,
#         "client_secret": settings.DISCORD_CLIENT_SECRET,
#         "grant_type": "refresh_token",
#         "refresh_token": refresh_token,
#         "redirect_uri": settings.DISCORD_REDIRECT_URI,
#         "scope": "identify"
#     }
#     headers = {
#         'Content-Type': 'application/x-www-form-urlencoded'
#     }
#     response = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
#     credentials = response.json()
#     access_token = credentials['access_token']
#     return access_token

def check_chaptcha(captcha_id, captcha_code):
    if captcha_id is None:
        raise ValidationError(message="Captcha code error, please refresh the page.")
    if captcha_code is None:
        raise ValidationError(message="Captcha code error, please refresh the page.")
    code_obj=CaptchaStore.objects.filter(id=captcha_id).first()
    if code_obj:
        expiration = code_obj.expiration
        expiration = expiration.astimezone(pytz.timezone("Asia/Shanghai"))
        response = code_obj.response
        code_obj.delete()
        five_minute_ago = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
        five_minute_ago = five_minute_ago.replace(tzinfo=pytz.timezone("Asia/Shanghai"))
        if five_minute_ago > expiration:
            raise ValidationError(message="Captcha code error, please refresh the page.")
        else:
            if response.lower() != captcha_code.lower():
                raise ValidationError(message="Captcha code error, please refresh the page.")
    else:
        raise ValidationError(message="Captcha code error, please refresh the page.")
