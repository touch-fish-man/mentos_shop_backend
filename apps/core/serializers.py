from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.request import Request
from rest_framework.serializers import ModelSerializer
from rest_framework.utils.serializer_helpers import BindingDict

from django_restql.mixins import DynamicFieldsMixin


class CommonSerializer(DynamicFieldsMixin, ModelSerializer):
    # 添加默认时间返回格式
    created_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", required=False, read_only=True
    )
    updated_at = serializers.DateTimeField(
        format="%Y-%m-%d %H:%M:%S", required=False
    )

    def __init__(self, instance=None, data=empty, request=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.request: Request = request or self.context.get("request", None)

    def save(self, **kwargs):
        return super().save(**kwargs)

    def create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    @property
    def errors(self):
        # get errors
        errors = super().errors
        verbose_errors = {}

        # fields = { field.name: field.verbose_name } for each field in model
        fields = {field.name: field.verbose_name for field in
                  self.Meta.model._meta.get_fields() if hasattr(field, 'verbose_name')}

        # iterate over errors and replace error key with verbose name if exists
        for field_name, error in errors.items():
            if field_name in fields:
                verbose_errors[str(fields[field_name])] = error
            else:
                verbose_errors[field_name] = error
        return verbose_errors
