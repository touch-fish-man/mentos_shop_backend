import base64
import hashlib
from datetime import datetime, timedelta

import pytz
from captcha.views import CaptchaStore, captcha_image
from captcha.models import CaptchaStore
from django.contrib import auth
from django.contrib.auth import authenticate, login, logout
from rest_framework import serializers
from apps.core.permissions import IsAuthenticated

# from apps.users.serializers import UserSerializer
from apps.core.json_response import SuccessResponse, ErrorResponse
from rest_framework.views import APIView
from apps.users.selectors import user_get_login_data
from .services import exchange_code, check_chaptcha
from django.shortcuts import redirect
from django.conf import settings
from apps.users.models import User
import urllib


class LoginApi(APIView):
    """
    用户登录
    post:登录
    get:获取登录状态
    """
    # 移除认证
    authentication_classes = ()

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        captcha_id = request.data.get('captcha_id')
        captcha_code = request.data.get('captcha')
        if not settings.DEBUG:
            check_chaptcha(captcha_id, captcha_code)
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            data = user_get_login_data(user=user)
            return SuccessResponse(data=data, msg="登录成功")
        else:
            return ErrorResponse(msg="用户名或密码错误", status=400)

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            data = user_get_login_data(user=user)
            return SuccessResponse(data=data, msg="获取成功")
        else:
            return ErrorResponse(msg="未登录", status=400)


class LogoutApi(APIView):
    """
    用户登出
    """
    permission_classes = [IsAuthenticated]
    def get(self, request):
        logout(request)
        return SuccessResponse(msg="登出成功")

    def post(self, request):
        logout(request)
        return SuccessResponse(msg="登出成功")


class DiscordOauth2LoginApi(APIView):
    """
    discord 登录
    """
    def get(self, request):
        client_id = settings.DISCORD_CLIENT_ID
        redirect_uri = settings.DISCORD_REDIRECT_URI
        if request.GET.get("mode") == "bind":
            redirect_uri = settings.DISCORD_BIND_REDIRECT_URI
        redirect_uri = urllib.parse.quote(redirect_uri)
        data = {
            'discord_auth_url': f'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=identify'}
        return SuccessResponse(data=data, msg="获取成功")


class DiscordOauth2RedirectApi(APIView):
    """
    discord 登录回调
    """
    def get(self, request):
        code = request.GET.get('code')
        if code is None:
            return ErrorResponse(msg="code错误", status=400)
        user = exchange_code(code, settings.DISCORD_REDIRECT_URI)
        if user is None:
            return ErrorResponse(msg="oauth错误", status=400)
        discord_id = user.get('id')
        # 查询用户是否存在
        user = User.objects.filter(discord_id=discord_id).first()

        if user is None:
            # 返回标志，前端跳转到注册页面，注册附带discord_id
            return redirect(f'/#/createAccount?discord_id={discord_id}')
        else:
            # 登录
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            # 重定向到用户页面
            return redirect("/#/dashboard/")


class DiscordBindRedirectApi(APIView):
    """
    discord绑定回调
    """
    def get(self, request):
        code = request.GET.get('code')
        if code is None:
            return ErrorResponse(msg="code错误")
        user = exchange_code(code, settings.DISCORD_BIND_REDIRECT_URI)
        if user is None:
            return ErrorResponse(msg="oauth错误")
        discord_id = user.get('id')
        discord_username = user.get('username')
        # 绑定用户
        user = request.user
        user.discord_id = discord_id
        user.discord_name = discord_username
        user.save()
        # 重定向到用户页面
        return redirect("/#/dashboard/")


class CaptchaApi(APIView):
    """
    验证码
    """

    def get(self, request):
        data = {}
        hashkey = CaptchaStore.generate_key()
        id = CaptchaStore.objects.filter(hashkey=hashkey).first().id
        imgage = captcha_image(request, hashkey)
        # 将图片转换为base64
        image_base = base64.b64encode(imgage.content)
        data = {
            "captcha_id": id,
            "captcha_image_base": "data:image/png;base64," + image_base.decode("utf-8"),
        }
        return SuccessResponse(data=data, msg="获取成功")


class ApiLoginSerializer(serializers.ModelSerializer):
    """接口文档登录-序列化器"""

    username = serializers.CharField()
    password = serializers.CharField()

    class Meta:
        model = User
        fields = ["username", "password"]


class ApiLogin(APIView):
    """接口文档的登录接口"""

    serializer_class = ApiLoginSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user_obj = auth.authenticate(
            request,
            username=username,
            password=hashlib.md5(password.encode(encoding="UTF-8")).hexdigest(),
        )
        if user_obj:
            login(request, user_obj)
            return redirect("/")
        else:
            return ErrorResponse(msg="账号/密码错误")
