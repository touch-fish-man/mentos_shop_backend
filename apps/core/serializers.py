from rest_framework import serializers

class CommonSerializer(serializers.Serializer):
    """
    通用序列化器
    """
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if hasattr(instance, 'created_at'):
            ret['created_at'] = instance.created_at.strftime('%Y-%m-%d %H:%M:%S')
        if hasattr(instance, 'updated_at'):
            ret['updated_at'] = instance.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        return ret