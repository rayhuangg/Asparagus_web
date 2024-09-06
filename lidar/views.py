import math
import sys
from os import path
from datetime import timedelta

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Scan, Lidar2D_ROS_data, Lidar2D_model
from .forms import ScanForm
from .serializers import Lidar2D_ROS_data_Serializer

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from record.models import ImageList, FrontView

# Create your views here.
def index(request):
    scan = Scan.objects.latest()
    points = scan.points
    data = []
    angle = -45
    for count, point in enumerate(points):
        x = point * math.cos(math.radians(angle))
        y = point * math.sin(math.radians(angle))
        angle += 0.25
        if abs(x) < 10000 and abs(y) < 10000:
            data.append({'x': x, 'y': y})

    return render(request, 'lidar/lidar.html', {'scan': scan, 'data': data})


@csrf_exempt
def scan(request):
    if request.method == 'POST':
        form = ScanForm(request.POST, request.FILES)
        if form.is_valid():
            points = [float(point) for point in dict(request.POST)['points']]
            front_image = FrontView.objects.latest()
            left_image = ImageList.objects.filter(section__name='test').latest()
            right_image = ImageList.objects.filter(section__name='test').latest()
            scan = Scan(front_image=front_image, left_image=left_image, right_image=right_image, points=points)
            scan.save()
        else:
            print(form.errors)

    else:
        form = ScanForm()

    return render(request, 'lidar/lidar.html', {'form': ScanForm})


class Lidar2dData(APIView):
    def post(self, request):
        serializer = Lidar2D_ROS_data_Serializer(data=request.data)

        if serializer.is_valid():
            lidar_model = serializer.validated_data['lidar_model']
            section = serializer.validated_data['section']
            ranges = serializer.validated_data['ranges']
            left_image = None
            right_image = None
            front_image = None

            def get_opposite_section(section_name) -> str:
                if section_name[0] in 'ABCDEFGH':
                    side = section_name[0]
                    number = section_name[1:]
                    if side in 'ACEG':
                        opposite_side = chr(ord(side) + 1)  # A -> B, C -> D, E -> F, G -> H
                    elif side in 'BDFH':
                        opposite_side = chr(ord(side) - 1)  # B -> A, D -> C, F -> E, H -> G
                    return f"{opposite_side}{number}"
                return None

            # Get the opposite section of the current section
            opposite_section = get_opposite_section(section.name)

            try:
                left_section_latest_image = ImageList.objects.filter(section__name__in=[section, opposite_section], side="left").latest('date')
                right_section_latest_image = ImageList.objects.filter(section__name__in=[section, opposite_section], side="right").latest('date')
                front_latest_image = FrontView.objects.latest('date')

                if now() - left_section_latest_image.date <= timedelta(seconds=3000000):
                    left_image = left_section_latest_image
                    print(f"{left_image = }, {left_image.section.name = }")
                else:
                    print("No left images found within the specified time interval.")

                if now() - right_section_latest_image.date <= timedelta(seconds=3000000):
                    right_image = right_section_latest_image
                    print(f"{right_image = }, {right_image.section.name = }")
                else:
                    print("No right images found within the specified time interval.")

                if now() - front_latest_image.date <= timedelta(seconds=30):
                    front_image = front_latest_image
                else:
                    print("No front images found within the specified time interval..")

            except ImageList.DoesNotExist:
                print("No side images found.")
            except FrontView.DoesNotExist:
                print("No front images found.")

            lidar_data = Lidar2D_ROS_data(
                lidar_model=lidar_model,
                section=section,
                ranges=ranges,
                create_time=now(),
                front_image=front_image,
                left_image=left_image,
                right_image=right_image
            )
            # lidar_data.save()
            # print(f"{lidar_data = }")

            print(f"{lidar_model = }, {section = }, {ranges = },  {len(ranges) = }")

            return Response({"message": "Data successfully saved."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)