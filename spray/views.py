import time
import json


from django.shortcuts import render
from .models import PesticideList, SprayExperimentRecord
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from channels.layers import get_channel_layer
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.core.cache import cache
import json


def index(request):
    return render(request, 'spray/spray.html')


# Fix experiment info.
# @csrf_exempt
@require_http_methods(["POST"])
def exp_info_update(request):
    data = request.POST
    location = data["location"]
    greenhouse = data["greenhouse"]
    pesticide = data["pesticide"]
    startime = time.time()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'VehicleStatusConsumer',
        {
            'type': 'vehicle.status',
            'message': data
        }
    )
    return HttpResponse(f"hello recieve{data}")


@require_POST
def update_vehicle_data(request):
    # Extract information from the JSON data in the request body
    data = json.loads(request.body)
    uwb_coordinates = data.get('uwb_coordinates')
    battery_level = data.get('battery_level')
    sprayed_pesticide  = data.get('sprayed_pesticide')
    remaining_pesticide = data.get('remaining_pesticide')

    # Construct a dictionary to store the data
    data = {
        'uwb_coordinates': uwb_coordinates,
        'battery_level': battery_level,
        'sprayed_pesticide': sprayed_pesticide,
        'remaining_pesticide': remaining_pesticide
    }
    print(data)
    # Cache the data with a timeout of 300 seconds
    cache.set('vehicle_status', data, timeout=600)
    return JsonResponse({'status': 'success'})


@require_GET
def get_vehicle_data(request):
    data = cache.get('vehicle_status')
    if data is not None:
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'No recent data'}, status=404)
