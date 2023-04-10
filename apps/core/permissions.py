from rest_framework.permissions import BasePermission
from django.contrib.auth import logout

class IsSuperUser(BasePermission):
    """
    Allows access only to superusers.
    """

    def has_permission(self, request, view):
        is_authenticated = request.user and request.user.is_authenticated
        if not is_authenticated:
            logout(request)
        return bool(request.user and request.user.is_superuser)
class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        is_authenticated = request.user and request.user.is_authenticated
        if not is_authenticated:
            logout(request)
        return is_authenticated
