from rest_framework.permissions import BasePermission,IsAuthenticated


class CustomPermission(BasePermission):
    """自定义权限"""

    def has_permission(self, request, view):
        # if isinstance(request.user, AnonymousUser):
        #     return False
        # 判断是否是超级管理员
        if request.user.is_superuser:
            return True
        else:
            return True