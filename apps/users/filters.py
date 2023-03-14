import django_filters
from apps.users.models import User
class BaseUserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = ("uid", "email", "is_admin")
