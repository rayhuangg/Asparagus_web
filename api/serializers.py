# api/serializers.py
from rest_framework import serializers
from monitor.models import ResultList

# Use serializers to determine what items to be seen in api result
class ResultListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultList
        # fields = '__all__'
        fields = ['date']