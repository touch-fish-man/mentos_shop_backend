from .models import Orders
from rest_framework import serializers
from apps.core.validators import CustomUniqueValidator
from ..proxy_server.models import Proxy


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = "__all__"




class OrdersUpdateSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(required=True, write_only=True)
    status = serializers.IntegerField(required=False)
    expired_at = serializers.DateTimeField(required=False)

    class Meta:
        model = Orders
        fields = ["order_id", "status", "expired_at"]


class OrdersListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = "__all__"
class OrdersStatusSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(required=True)

    class Meta:
        model = Orders
        fields = ["order_id", "pay_status"]

class ProxyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proxy
        fields = "__all__"
