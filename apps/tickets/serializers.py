import datetime

from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Tickets, Question
from django.core.validators import validate_email


class TicketsSerializer(serializers.ModelSerializer):
    captcha = serializers.CharField(max_length=6, required=False, write_only=True, )
    captcha_id = serializers.CharField(max_length=36, required=False, write_only=True, )
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tickets
        fields = "__all__"

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError as exc:
            raise serializers.ValidationError(str(exc))
        return value

    def save(self, **kwargs):
        kwargs.pop('captcha', None)
        kwargs.pop('captcha_id', None)
        instance = super().save(**kwargs)
        return instance


class FQASerializer(serializers.Serializer):
    class Meta:
        model = Question
        fields = "__all__"
