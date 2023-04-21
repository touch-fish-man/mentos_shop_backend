from rest_framework import serializers
from apps.rewards.models import CouponCode, PointRecord, GiftCard,LevelCode
from apps.users.models import User
from apps.core.serializers import CommonSerializer


class CouponCodeSerializer(serializers.ModelSerializer):
    """
    优惠码
    """
    class Meta:
        model = CouponCode
        fields = '__all__'
# class CouponCodeCreateSerializer(serializers.ModelSerializer):
#     """
#     创建优惠码
#     """

#     class Meta:
#         model = CouponCode
#         fields = ('code', 'discount', 'code_type', 'holder_username')

#     def save(self, **kwargs):
#         holder_username = kwargs.get("holder_username")
#         holder_uid = User.objects.filter(user__username=holder_username).get("id")
#         kwargs["holder_uid"] = holder_uid
#         return super().save(**kwargs)
class CouponCodeCreateSerializer(CommonSerializer):
    """
    创建优惠码
    """
    def create(self, validated_data):
        user = User.objects.filter(username=validated_data['holder_username']).first()
        validated_data['holder_uid'] = user.id
        return super().create(validated_data)

    class Meta:
        model = CouponCode
        fields = ('code', 'discount', 'code_type', 'holder_username')

class PointRecordSerializer(serializers.ModelSerializer):
    """
    兑换记录
    """
    class Meta:
        model = PointRecord
        fields = '__all__'
class GiftCardSerializer(serializers.ModelSerializer):
    """
    礼品卡
    """
    class Meta:
        model = GiftCard
        fields = '__all__'
class LevelCodeSerializer(serializers.ModelSerializer):
    """
    等级码
    """
    class Meta:
        model = LevelCode
        fields = '__all__'