import django_filters
from apps.tickets.models import WorkOrder

class BaseWorkOrderFilter(django_filters.FilterSet):
    class Meta:
        model = WorkOrder
        fields = ("username", "phone", "email")
