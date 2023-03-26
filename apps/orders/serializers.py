from .models import Orders
from rest_framework import serializers
from apps.core.validators import CustomUniqueValidator


class OrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = "__all__"


class OrdersCreateSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(required=True, write_only=True)
    product_num = serializers.IntegerField(required=True, write_only=True, validators=[])

    class Meta:
        model = Orders
        fields = ["product_id", "product_num", "order_id"]
        extra_kwargs = {
            "product_num": {"required": True},
        }

    def validate_product_id(self, value):
        if not value:
            raise serializers.ValidationError("产品id不能为空")
        # 验证产品id是否存在
        if not Orders.objects.filter(product_id=value).exists():
            raise serializers.ValidationError("产品不存在")
        return value

    def validate_product_num(self, value):
        if not value:
            raise serializers.ValidationError("产品数量不能为空")
        # 验证产品数量是否大于0
        if value <= 0:
            raise serializers.ValidationError("产品数量不能小于0")
        # todo 验证产品数量是否大于库存
        # if value > Products.objects.filter(product_id=self.product_id).first().product_num:
        #     raise serializers.ValidationError("产品数量不能大于库存")
        return value

    def create(self, validated_data):
        # fixme 获取当前用户id
        # if self.context["request"].user.is_authenticated:
        #     raise serializers.ValidationError("请先登录")
        validated_data["uid"] = self.context["request"].user.id
        validated_data["username"] = self.context["request"].user.username
        return Orders.objects.create(**validated_data)


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
