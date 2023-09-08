from rest_framework import serializers
from monitor.models import ResultList

class ResultListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultList
        fields = '__all__'