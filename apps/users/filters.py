import django_filters
from apps.users.models import User, WorkOrder
class BaseUserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = ("uid", "email", "is_superuser", "level", "is_active", "username")

class BaseWorkOrderFilter(django_filters.FilterSet):
    class Meta:
        model = WorkOrder
        fields = ("username", "phone", "email")
