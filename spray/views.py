import time
import json


from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .models import FertilizerList, SprayExperimentRecord
from .serializers import SprayExperimentRecordSerializer


# Main front view page entrance.
def index(request):
    return render(request, "spray/spray.html")



@api_view(['POST'])
def update_experiment_info(request):
    data = request.data
    status = data.get('status', None)
    print(f"{data = }")

    if status == 'start':
        # 檢查最新的一筆資料是否有 end_time，若無，設定其 end_time
        # last_record = SprayExperimentRecord.objects.last()
        # if last_record and not last_record.end_time:
        #     last_record.end_time = now()
        #     last_record.save()

        # 創建新的實驗記錄
        serializer = SprayExperimentRecordSerializer(data=data['content'])
        if serializer.is_valid():
            # serializer.save(start_time=now())
            print(f"{serializer.data = }")
            return Response(serializer.data, status=201)
        else:
            print(f"{serializer.errors = }")
            return Response(serializer.errors, status=400)

    elif status == 'end':
        # 將 end_time 設定為目前時間，並更新 fertilizer_total_amount
        last_record = SprayExperimentRecord.objects.last()
        if last_record:
            update_data = {
                'end_time': now(),
                'fertilizer_total_amount': data['content'].get('fertilizer_total_amount')
            }
            serializer = SprayExperimentRecordSerializer(last_record, data=update_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            else:
                return Response(serializer.errors, status=400)
        else:
            return Response({'error': 'No active experiment to end'}, status=404)


# REST API for getting and updating vehicle real-time data
class VehicleRealTimeData(APIView):
    def get(self, request):
        data = cache.get("vehicle_status")
        # TODO
        # 加上上次實驗時間地點(DB)
        if data is not None:
            return Response(data)
        else:
            return Response({"error": "No recent data"}, status=404)

    def post(self, request):
        # Extract information from the JSON data in the request body,
        # REST API does not support form data type, used body instead
        print(data)
        uwb_coordinates = data.get("uwb_coordinates")
        battery_level = data.get("battery_level")
        sprayed_pesticide = data.get("sprayed_pesticide")
        remaining_pesticide = data.get("remaining_pesticide")

        # Construct a dictionary to store the data
        data = {
            "uwb_coordinates": uwb_coordinates,
            "battery_level": battery_level,
            "sprayed_pesticide": sprayed_pesticide,
            "remaining_pesticide": remaining_pesticide,
        }
        # Cache the data with a timeout of 600 seconds
        cache.set("vehicle_status", data, timeout=600)
        return Response({"status": "success"})




def retrive_lication_list(request):
    pass

def retrive_greenhouse_list(request):
    pass

def retrive_fertilizer_list(request):
    pass