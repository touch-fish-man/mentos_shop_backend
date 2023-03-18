import base64
import string
import time
import random

from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin

from django.core.validators import validate_email
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.users.models import User, Code
from apps.users.selectors import user_get_login_data, user_list
from rest_framework import serializers
from rest_framework import status
from apps.api.pagination import LimitOffsetPagination, get_paginated_response
from apps.users.service import send_email_code
from captcha.views import CaptchaStore, captcha_image


class UserInfoApi(LoginRequiredMixin, APIView):
    """
    用户信息路由
    """

    def get(self, request):
        user = request.user
        print(user)
        data = user_get_login_data(user=user)
        return Response(data)

    def post(self, request):
        user = request.user
        email = request.data.get('email')
        user.email = email
        user.save()
        return Response({'status': 'success'}, status=200)

    def delete(self, request):
        user = request.user
        user.delete()
        return Response({'status': 'success'}, status=200)

    def put(self, request):
        user = request.user
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        user.username = username
        user.password = make_password(password)
        user.email = email
        user.save()
        return Response({'status': 'success'}, status=200)


class UserListApi(APIView):
    """
    用户列表路由
    """

    class Pagination(LimitOffsetPagination):
        default_limit = 1

    class FilterSerializer(serializers.Serializer):
        id = serializers.IntegerField(required=False)
        is_admin = serializers.BooleanField(required=False, allow_null=True, default=None)
        email = serializers.EmailField(required=False)

    class OutputSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ("id", "email", "is_admin")

    def get(self, request):
        # Make sure the filters are valid, if passed
        filters_serializer = self.FilterSerializer(data=request.query_params)
        filters_serializer.is_valid(raise_exception=True)

        users = user_list(filters=filters_serializer.validated_data)

        return get_paginated_response(
            pagination_class=self.Pagination,
            serializer_class=self.OutputSerializer,
            queryset=users,
            request=request,
            view=self,
        )


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
        return Response({'status': True, 'msg': 'register success'}, status=200)

    def get(self, request):
        return Response({'status': 'success'}, status=200)


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
        return Response({'status': 'success', 'data': data})


class EmailValidateApi(APIView):
    """
    邮箱验证路由
    """

    def post(self, request):
        email = request.data.get('email')
        try:
            validate_email(email)
        except:
            return Response({"status": status.HTTP_400_BAD_REQUEST, "msg": "email format error", "data": {}})
        send_success = send_email_code(email)
        if send_success:
            response = {"status": status.HTTP_200_OK, "msg": "sending success", "data": {}}
        else:
            response = {"status": status.HTTP_400_BAD_REQUEST, "msg": "sending fail", "data": {}}

        return Response(response)
