from rest_framework import serializers
from .models import SprayExperimentRecord, FertilizerList, FertilizerUsage
from django.utils.timezone import now


class FertilizerUsageSerializer(serializers.ModelSerializer):
    fertilizer_id = serializers.PrimaryKeyRelatedField(queryset=FertilizerList.objects.all(), source='fertilizer', write_only=True)
    amount = serializers.FloatField()
    fertilizer_name = serializers.CharField(source='fertilizer.name', read_only=True)

    class Meta:
        model = FertilizerUsage
        fields = ['fertilizer_id', 'amount', 'fertilizer_name']


class SprayExperimentRecordSerializer(serializers.ModelSerializer):
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    fertilizer_usages = FertilizerUsageSerializer(many=True, read_only=True)
    total_water_used = serializers.FloatField(required=False, allow_null=True)
    fertilizer_usage_summary = serializers.SerializerMethodField()

    class Meta:
        model = SprayExperimentRecord
        fields = ['location', 'greenhouse', 'fertilizer_usages', 'total_water_used', 'start_time', 'end_time', 'note', 'fertilizer_usage_summary']

    # 定義方法來返回模型中的 `get_fertilizer_usage` 結果
    def get_fertilizer_usage_summary(self, obj):
        return obj.get_fertilizer_usage()


    def create(self, validated_data):
        fertilizers_data = self.context['request'].data.get('fertilizers', [])
        experiment = SprayExperimentRecord.objects.create(**validated_data)
        for fertilizer_data in fertilizers_data:
            FertilizerUsage.objects.create(experiment=experiment, fertilizer_id=fertilizer_data['id'], amount=fertilizer_data['amount'])
        return experiment


    def update(self, instance, validated_data):
        # Implement similar logic for update if necessary
        return super().update(instance, validated_data)


class FertilizerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FertilizerList
        fields = ['id', 'name']


