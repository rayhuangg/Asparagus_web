from rest_framework import serializers
from .models import SprayExperimentRecord, FertilizerList, FertilizerUsage
from django.utils.timezone import now


class FertilizerUsageSerializer(serializers.ModelSerializer):
    fertilizer_id = serializers.PrimaryKeyRelatedField(queryset=FertilizerList.objects.all(), source='fertilizer', write_only=True)
    amount = serializers.FloatField()

    class Meta:
        model = FertilizerUsage
        fields = ['fertilizer_id', 'amount']


class SprayExperimentRecordSerializer(serializers.ModelSerializer):
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    fertilizers = FertilizerUsageSerializer(many=True, write_only=True)  # 只在 "開始" 時寫入藥肥使用量
    total_water_used = serializers.FloatField(required=False, allow_null=True)  # 僅在 "結束" 時記錄總用水量

    class Meta:
        model = SprayExperimentRecord
        fields = ['location', 'greenhouse', 'fertilizers', 'total_water_used', 'start_time', 'end_time', 'note']

    def create(self, validated_data):
        fertilizers_data = validated_data.pop('fertilizers')  # 從資料中取出 fertilizers
        experiment = SprayExperimentRecord.objects.create(**validated_data)  # 創建實驗記錄
        for fertilizer_data in fertilizers_data:
            FertilizerUsage.objects.create(experiment=experiment, **fertilizer_data)  # 創建每種藥肥的使用記錄
        return experiment

    def update(self, instance, validated_data):
        # Implement similar logic for update if necessary
        return super().update(instance, validated_data)


class FertilizerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FertilizerList
        fields = ['id', 'name']


