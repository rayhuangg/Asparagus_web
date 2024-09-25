import time
import json
import requests

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.pagination import PageNumberPagination


from .models import FertilizerList, SprayExperimentRecord
from .serializers import SprayExperimentRecordSerializer, FertilizerListSerializer


# Main front view page entrance.
def index(request):
    return render(request, "spray/spray.html")


@api_view(['POST'])
def update_experiment_info(request):
    data = request.data
    status = data.get('status', None)

    if status == 'start':
        # Check whether the latest data has end_time, if not, set its end_time
        last_record = SprayExperimentRecord.objects.last()
        if last_record and not last_record.end_time:
            last_record.end_time = now()
            last_record.save()

        # Create new experiment record
        serializer = SprayExperimentRecordSerializer(data=data['content'])
        if serializer.is_valid():
            serializer.save(start_time=now())
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)

    elif status == 'end':
        # Update the experiment with end_time, total water used, and fertilizer usages
        last_record = SprayExperimentRecord.objects.last()
        if last_record:
            if last_record.end_time:
                return Response({'error': 'The last experiment has already ended'}, status=400)
            else:
                update_data = {
                    'end_time': now(),
                    'total_water_used': data['content'].get('total_water_used'),
                }
                serializer = SprayExperimentRecordSerializer(last_record, data=update_data, partial=True)
                if serializer.is_valid():
                    serializer.save()

                    # Upload the spray data to the Professor Cheng-Ying Chou pest detection server
                    spray_target = data['content'].get('spray_target')
                    if spray_target:
                        try:
                            upload_spray_to_professor_chou(spray_target)
                        except Exception as e:
                            return Response({'error': f"Failed to upload spray data: {str(e)}"}, status=500)

                    return Response(serializer.data, status=200)
                else:
                    return Response(serializer.errors, status=400)
        else:
            return Response({'error': 'No active experiment to end'}, status=404)

    else:
        return Response({'error': 'Invalid status, status should be start or stop'}, status=400)

# Upload the exp data to the Professor Cheng-Ying Chou pest detection server.
def upload_spray_to_professor_chou(sprayed_list: list):
    # 楊詠仁溫室設備名稱
    # yang-left1, yang-left2, yang-left3, yang-middle1, yang-middle2, yang-middle3, yang-right1, yang-right2, yang-right3

    # 黃彥碩溫室設備名稱
    # huang-left1, huang-left2, huang-left3, huang-middle1, huang-middle2, huang-middle3, huang-right1, huang-right2, huang-right3

    url = "https://asparagus.agriweather.tw/api/pest/tasks"

    for device in sprayed_list:
        data = {
            "deviceHash": device,
            "status": "done"
        }
        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, data=json.dumps(data), headers=headers)

        if response.status_code == 200:
            print(f"device: {device} upload successfully")
        else:
            raise Exception(f"ERROR: device: {device}, Status Code: {response.status_code}, Response: {response.text}")



# REST API for getting and updating vehicle real-time data
class VehicleRealTimeData(APIView):
    BATTERY_LEVEL_MIN = 0
    BATTERY_LEVEL_MAX = 100
    PESTICIDE_MIN = 0

    def get(self, request):
        data = cache.get("vehicle_status")
        # TODO
        # 加上上次實驗時間地點(DB)

        # TODO: 加入前端顯示
        if data is not None:
            return Response(data)
        else:
            return Response({"error": "No recent data"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        # Extract information from the JSON data in the request body,
        # REST API does not support form data type, used body instead
        data = request.data
        uwb_coordinates = data.get("uwb_coordinates")
        battery_level = data.get("battery_level")
        sprayed_pesticide = data.get("sprayed_pesticide")
        remaining_pesticide = data.get("remaining_pesticide")

        if (uwb_coordinates is not None) and (len(uwb_coordinates) != 2):
            return Response({"status": "error", "message": "Invalid uwb_coordinates"}, status=status.HTTP_400_BAD_REQUEST)

        if battery_level is None or not (self.BATTERY_LEVEL_MIN <= battery_level <= self.BATTERY_LEVEL_MAX):
            return Response({"status": "error", "message": "Invalid or missing battery_level"}, status=status.HTTP_400_BAD_REQUEST)

        if sprayed_pesticide is None or not (self.PESTICIDE_MIN <= sprayed_pesticide):
            return Response({"status": "error", "message": "Invalid or missing sprayed_pesticide"}, status=status.HTTP_400_BAD_REQUEST)

        if remaining_pesticide is None or not (self.PESTICIDE_MIN <= remaining_pesticide):
            return Response({"status": "error", "message": "Invalid or missing remaining_pesticide"}, status=status.HTTP_400_BAD_REQUEST)


        # Construct a dictionary to store the data
        data = {
            "uwb_coordinates": uwb_coordinates,
            "battery_level": battery_level,
            "sprayed_pesticide": sprayed_pesticide,
            "remaining_pesticide": remaining_pesticide,
        }
        # Cache the data with a timeout of 600 seconds
        cache.set("vehicle_status", data, timeout=600) # TODO:記得改回來
        return Response({"status": "success"}, status=status.HTTP_200_OK)


class SprayExperimentRecordPagination(PageNumberPagination):
    page_size = 3

class SprayExperimentRecordListView(generics.ListCreateAPIView):
    queryset = SprayExperimentRecord.objects.all().order_by('-experiment_id')
    serializer_class = SprayExperimentRecordSerializer
    pagination_class = SprayExperimentRecordPagination


class FertilizerListView(APIView):
    def get(self, request):
        fertilizers = FertilizerList.objects.all()
        serializer = FertilizerListSerializer(fertilizers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FertilizerListSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data.get('name')
            if FertilizerList.objects.filter(name=name).exists():
                return Response({'name': 'A fertilizer with this name already exists.'}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
