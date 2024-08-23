import time
import json

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
        # 檢查最新的一筆資料是否有 end_time，若無，設定其 end_time
        last_record = SprayExperimentRecord.objects.last()
        if last_record and not last_record.end_time:
            last_record.end_time = now()
            last_record.save()

        # 創建新的實驗記錄
        serializer = SprayExperimentRecordSerializer(data=data['content'])
        if serializer.is_valid():
            serializer.save(start_time=now())
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)

    elif status == 'end':
        # 將 end_time 設定為目前時間，並更新 fertilizer_total_amount
        last_record = SprayExperimentRecord.objects.last()
        if last_record:
            if last_record.end_time:
                return Response({'error': 'The last experiment has already ended'}, status=400)
            else:
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
        cache.set("vehicle_status", data, timeout=6000) # TODO:記得改回來
        return Response({"status": "success"}, status=status.HTTP_200_OK)


def retrive_location_list(request):
    pass

def retrive_greenhouse_list(request):
    pass

# def retrive_exp_history(request):
#     if request.method == "GET":
#         context = []
#         results = SprayExperimentRecord.objects.all()


# def preview(request):
#     if request.method == 'POST':
#         context = []
#         sec = request.POST['section']
#         imgs = ImageList.objects.filter(section__name=sec)[:3]
#         for img in imgs:
#             context.append({'name': img.name, 'date': img.date.astimezone(pytz.timezone('Asia/Taipei')).strftime('%Y.%m.%d %H:%M:%S'), 'id': img.id, 'url': img.image.url})
#         return HttpResponse(json.dumps({'context': context}))


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
