from rest_framework import serializers
from .models import SprayExperimentRecord, FertilizerList
from django.utils.timezone import now


class SprayExperimentRecordSerializer(serializers.ModelSerializer):
    end_time = serializers.DateTimeField(required=False, allow_null=True)
    fertilizer_total_amount = serializers.FloatField(required=False, allow_null=True)

    class Meta:
        model = SprayExperimentRecord
        fields = ['location', 'greenhouse', 'fertilizer', 'start_time', 'end_time', 'fertilizer_total_amount']
        extra_kwargs = {
            'location': {'required': True},
            'greenhouse': {'required': True},
            'fertilizer': {'required': True},
            'start_time': {'required': False, 'default': now}
        }

    def create(self, validated_data):
        fertilizers_data = validated_data.pop('fertilizer')
        experiment = SprayExperimentRecord.objects.create(**validated_data)
        for fert_name in fertilizers_data:
            try:
                fertilizer = FertilizerList.objects.get(name=fert_name)
            except FertilizerList.DoesNotExist:
                raise serializers.ValidationError()
            experiment.fertilizer.add(fertilizer)
        return experiment

    def update(self, instance, validated_data):
        # Implement similar logic for update if necessary
        return super().update(instance, validated_data)


class FertilizerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FertilizerList
        fields = ['id', 'name']