from apps.tickets.models import WorkOrder
from django.db.models.query import QuerySet
from apps.tickets.filters import BaseWorkOrderFilter

def workorder_list(*,filters=None) -> QuerySet[WorkOrder]:
    filter = filters or {}

    qs = WorkOrder.objects.all()

    return BaseWorkOrderFilter(filter, qs).qs