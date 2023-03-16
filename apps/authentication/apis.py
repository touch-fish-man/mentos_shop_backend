from django.contrib.auth import authenticate, login, logout
# from apps.users.serializers import UserSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apps.users.selectors import user_get_login_data
from .service import exchange_code
from django.shortcuts import redirect
from django.conf import settings
from ..users.models import User


class LoginApi(APIView):
    def post(self, request):
        # UserSerializer(data=request.data)
        username = request.data.get('username')
        password = request.data.get('password')
        code = request.data.get('code')
        if code != '1234':
            return Response(status=status.HTTP_400_BAD_REQUEST, data={'msg': '验证码错误'})
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            session_key = request.session.session_key
            data = user_get_login_data(user=user)
            return Response({'session': session_key, "data": data})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        return Response({'status': 'success'})


class LogoutApi(APIView):
    def get(self, request):
        logout(request)
        return Response()

    def post(self, request):
        logout(request)
        return Response()


class DiscordOauth2LoginApi(APIView):
    def get(self, request):
        client_id=settings.DISCORD_CLIENT_ID
        redirect_uri=settings.DISCORD_REDIRECT_URI
        redirect_uri =urllib.parse.quote(redirect_uri)
        return Response({'discord_auth_url': f'https://discord.com/api/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=identify'})


class DiscordOauth2RedirectApi(APIView):
    def get(self, request):
        code = request.GET.get('code')
        if code is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = exchange_code(code)
        if user is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        discord_id = user.get('id')
        # 查询用户是否存在
        user = User.objects.filter(discord_id=discord_id).first()
        if user is None:
            # 返回标志，前端跳转到注册页面，注册附带discord_id
            return Response({'status': 'register', 'discord_id': discord_id})
        else:
            # 登录
            discord_user = authenticate(request, user=user)
            login(request, discord_user)
            # 重定向到用户页面
            return redirect("/dashboard/")
