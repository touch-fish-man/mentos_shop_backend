from django.contrib.auth.hashers import make_password
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.users.models import User
from apps.users.selectors import user_get_login_data, user_list
from rest_framework import serializers
from rest_framework import status
from apps.api.pagination import LimitOffsetPagination, get_paginated_response


class UserInfoApi(LoginRequiredMixin,APIView):
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
        code = request.data.get('code')
        if code != '1234':
            return Response({'status': 'fail'}, status=400)
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()
        return Response({'status': 'success', 'msg': 'register success'}, status=200)

    def get(self, request):
        return Response({'status': 'success'}, status=200)


class CaptchaApi(APIView):
    """
    验证码路由
    """

    def get(self, request):
        return Response({'status': 'success'}, status=200)

    def post(self, request):
        return Response({'status': 'success'}, status=200)
