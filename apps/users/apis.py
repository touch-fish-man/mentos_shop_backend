import base64
import time

from captcha.views import CaptchaStore, captcha_image
from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.validators import validate_email
from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.json_respon import JsonResponse, ErrorResponse
from apps.users.models import User, Code
from apps.users.selectors import user_get_login_data
from .services import send_email_code


class UserInfoApi(LoginRequiredMixin, APIView):
    """
    用户信息路由
    """

    def get(self, request):
        user = request.user
        print(user)
        data = user_get_login_data(user=user)
        return JsonResponse(data=data, msg="获取成功")

    def post(self, request):
        user = request.user
        email = request.data.get('email')
        user.email = email
        user.save()
        return JsonResponse(msg="修改成功")

    def delete(self, request):
        user = request.user
        user.delete()
        return JsonResponse(msg="删除成功")

    def put(self, request):
        user = request.user
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        user.username = username
        user.password = make_password(password)
        user.email = email
        user.save()
        return JsonResponse(msg="修改成功")


class UserListApi(ListAPIView, LoginRequiredMixin):
    """
    用户列表路由
    """

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ("id", "uid", "username", "email", "is_superuser", "level", "is_active", "points", "date_joined","discord_id","last_login")

        def to_representation(self, instance):
            ret = super().to_representation(instance)
            ret['date_joined'] = instance.date_joined.strftime('%Y-%m-%d %H:%M:%S')
            ret['last_login'] = instance.last_login.strftime('%Y-%m-%d %H:%M:%S')
            if instance.discord_id:
                ret['discord_id'] = instance.discord_id
            else:
                ret['discord_id'] = ""
            return ret

    serializer_class = OutputSerializer
    ordering_fields = ('id', 'uid', 'username', 'email', 'level', 'is_active')
    search_fields = ('username', 'email')  # 搜索字段
    filterset_fields = ['uid', 'username', 'email', 'is_superuser', 'level', 'is_active']  # 过滤字段
    queryset = User.objects.all()

    def post(self, request):
        user = request.user
        if user.is_superuser:
            username = request.data.get('username')
            password = request.data.get('password')
            email = request.data.get('email')
            invite_code = request.data.get('invite_code')
            user = User.objects.create_user(username=username, password=password,
                                            email=email, invite_code=invite_code)
            user.save()
            return JsonResponse(msg="添加成功")
        else:
            return JsonResponse(msg="无权限")

    def put(self, request):
        user = request.user
        if user.is_superuser:
            uid = request.data.get('uid')
            is_active = request.data.get('is_active')
            is_superuser = request.data.get('is_superuser')
            user = User.objects.get(uid=uid)
            user.is_active = is_active
            user.is_superuser = is_superuser
            user.save()
            return JsonResponse(msg="修改成功")
        else:
            return JsonResponse(msg="无权限")

    def delete(self, request):
        user = request.user
        if user.is_superuser:
            uid = request.data.get('uid')
            user = User.objects.get(uid=uid)
            user.delete()
            return JsonResponse(msg="删除成功")
        else:
            return JsonResponse(msg="无权限")


class UserRegisterApi(APIView):
    """
    用户注册路由
    """

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        invite_code = request.data.get('invite_code')
        email_code = request.data.get('email_code')
        queryset = Code.objects.filter(email=email)
        if queryset.exists():
            db_code = queryset.order_by('-create_time').first()
        else:
            return Response({'status': False, 'msg': 'email error'}, status=200)
        time_now = int(time.time())
        del_time = time_now - db_code.create_time
        if del_time >= 600:
            db_code = Code.objects.filter(email=email)
            db_code.delete()
            return Response({'status': False, 'msg': 'code overdue'}, status=200)
        if email_code != db_code.code:
            return Response({'status': False, 'msg': 'code fail'}, status=200)
        user = User.objects.create_user(username=username, password=password,
                                        email=email, invite_code=invite_code)
        user.save()
        db_code = Code.objects.filter(email=email)
        db_code.delete()
        return JsonResponse(msg="注册成功")


class CaptchaApi(APIView):
    """
    验证码路由
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
        return JsonResponse(data=data, msg="获取成功")


class EmailValidateApi(APIView):
    """
    邮箱验证路由
    """

    def post(self, request):
        email = request.data.get('email')
        try:
            validate_email(email)
        except:
            return ErrorResponse(msg="email error")
        send_success = send_email_code(email)
        if send_success:
            msg = "send success"
            data = {}
            return JsonResponse(data=data, msg=msg)
        else:
            msg = "send fail"
            data = {}
            return ErrorResponse(data=data, msg=msg)
