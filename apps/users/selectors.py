from apps.users.models import User
from django.db.models.query import QuerySet
from apps.users.filters import BaseUserFilter


def user_get_login_data(*, user: User):
    return {
        "id": user.id,
        "uid": user.uid,
        "email": user.email,
        "username": user.username,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "discord_id":user.discord_id if len(user.discord_id) else None,
        "discord_name": user.discord_name if len(user.discord_name) else None,
    }


def user_list(*, filters=None) -> QuerySet[User]:
    filters = filters or {}

    qs = User.objects.all()

    return BaseUserFilter(filters, qs).qs
