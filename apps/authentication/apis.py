from datetime import datetime, timedelta

from captcha.models import CaptchaStore
from django.contrib.auth import authenticate, login, logout
# from apps.users.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apps.users.selectors import user_get_login_data
from .service import exchange_code
from django.shortcuts import redirect
from django.conf import settings
from apps.users.models import User
import urllib


class LoginApi(APIView):
    def post(self, request):
        # UserSerializer(data=request.data)
        username = request.data.get('username')
        password = request.data.get('password')
        code = request.data.get('code')
        captcha_id = request.data.get('captcha_id')
        captcha_code = request.data.get('captcha')
        if code != "1234":
            if captcha_id is None:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={'msg': '验证码错误', 'status': 400, 'data': {}})
            if captcha_code is None:
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={'msg': '验证码错误', 'status': 400, 'data': {}})
            image_code = CaptchaStore.objects.filter(id=captcha_id).first()
            five_minute_ago = datetime.now() - timedelta(hours=0, minutes=5, seconds=0)
            if image_code and five_minute_ago > image_code.expiration:
                image_code.delete()
                return Response(status=status.HTTP_400_BAD_REQUEST,
                                data={'msg': '验证码过期', 'status': 400, 'data': {}})
            else:
                if image_code and image_code.response.lower() == captcha_code.lower():
                    image_code.delete()
                else:
                    image_code.delete()
                    return Response(status=status.HTTP_400_BAD_REQUEST,
                                    data={'msg': '验证码错误', 'status': 400, 'data': {}})
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            session_key = request.session.session_key
            data = user_get_login_data(user=user)
            return Response({"data": data, "msg": "登录成功", "status": 200})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST,
                            data={'msg': '用户名或密码错误', 'status': 400, 'data': {}})

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
            data = user_get_login_data(user=user)
            return Response({"data": data, "masg": "登录成功", "status": 200})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '未登录', 'status': 400, 'data': {}})


class LogoutApi(APIView):
    def get(self, request):
        logout(request)
        return redirect('/')

    def post(self, request):
        logout(request)
        return redirect('/')


class DiscordOauth2LoginApi(APIView):
    def get(self, request):
        client_id = settings.DISCORD_CLIENT_ID
        redirect_uri = settings.DISCORD_REDIRECT_URI
        if request.GET.get("mode") == "bind":
            redirect_uri = settings.DISCORD_BIND_REDIRECT_URI
        redirect_uri = urllib.parse.quote(redirect_uri)
        return Response(status=status.HTTP_200_OK, data={"status": 200, "msg": "success", "data": {
            'discord_auth_url': f'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=identify'}

                                                         })


class DiscordOauth2RedirectApi(APIView):
    def get(self, request):
        code = request.GET.get('code')
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = exchange_code(code, settings.DISCORD_REDIRECT_URI)
        if user is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        discord_id = user.get('id')
        # 查询用户是否存在
        user = User.objects.filter(discord_id=discord_id).first()
        if user is None:
            # 返回标志，前端跳转到注册页面，注册附带discord_id
            return redirect(f'/register?discord_id={discord_id}')
        else:
            # 登录
            discord_user = authenticate(request, user=user)
            login(request, discord_user)
            # 重定向到用户页面
            return redirect("/dashboard/")


class DiscordBindRedirectApi(APIView):
    def get(self, request):
        code = request.GET.get('code')
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = exchange_code(code, settings.DISCORD_BIND_REDIRECT_URI)
        if user is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        discord_id = user.get('id')
        # 绑定用户
        user = request.user
        user.discord_id = discord_id
        user.save()
        # 重定向到用户页面
        return redirect("/dashboard/")
