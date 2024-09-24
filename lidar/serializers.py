from rest_framework import serializers
from record.models import Section
from .models import Lidar2D_ROS_data, Lidar2D_model



class Lidar2D_ROS_data_Serializer(serializers.ModelSerializer):
    lidar_model = serializers.CharField()
    section = serializers.CharField()

    class Meta:
        model = Lidar2D_ROS_data
        fields = ["lidar_model", "ranges", "section", "side"]

    def validate(self, data):
        model_name = data.get('lidar_model')
        section_name = data.get('section')
        side = data.get('side')

        if model_name:
            try:
                lidar_model = Lidar2D_model.objects.get(model_name=model_name)
            except Lidar2D_model.DoesNotExist:
                raise serializers.ValidationError({"lidar_model": "Lidar model does not exist."})
            data['lidar_model'] = lidar_model

        if section_name:
            try:
                section = Section.objects.get(name=section_name)
            except Section.DoesNotExist:
                raise serializers.ValidationError({"section": "Section does not exist."})
            data['section'] = section

        if not isinstance(data.get('ranges'), list) or not data['ranges']:
            raise serializers.ValidationError({"ranges": "Ranges must be a non-empty list."})

        if side and side not in ["left", "right"]:
            raise serializers.ValidationError({"side": "Side must be either 'left' or 'right'."})
        else:
            data['side'] = side

        return data