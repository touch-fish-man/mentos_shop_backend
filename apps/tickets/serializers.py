import datetime

from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Tickets
from django.core.validators import validate_email


class TicketsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tickets
        fields = "__all__"
    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        return value
