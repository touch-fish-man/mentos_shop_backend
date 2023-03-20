from apps.users.models import User, WorkOrder
from django.db.models.query import QuerySet
from apps.users.filters import BaseUserFilter, BaseWorkOrderFilter


def user_get_login_data(*, user: User):
    return {
        "uid": user.uid,
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }


def user_list(*, filters=None) -> QuerySet[User]:
    filters = filters or {}

    qs = User.objects.all()

    return BaseUserFilter(filters, qs).qs

def workorder_list(*,filters=None) -> QuerySet[WorkOrder]:
    filter = filters or {}

    qs = WorkOrder.objects.all()

    return BaseWorkOrderFilter(filter, qs).qs