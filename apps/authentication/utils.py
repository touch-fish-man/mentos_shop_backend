from django.contrib.auth.backends import ModelBackend

from apps.users.models import User


class AuthBackend(ModelBackend):
    # 重写authenticate方法
    # email和username都可以登录
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        if user.check_password(password):
            return user
        else:
            return None