import math
import sys
from os import path
from datetime import timedelta
from typing import Tuple, Optional

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
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


def get_opposite_section(section_name) -> str:
    '''
    Get the opposite section of the current section.
    For example, if the current section is 'A1', the opposite section is 'B1'.
    '''
    if section_name[0] in 'ABCDEFGH':
        side = section_name[0]
        number = section_name[1:]
        if side in 'ACEG':
            opposite_side = chr(ord(side) + 1)  # A -> B, C -> D, E -> F, G -> H
        elif side in 'BDFH':
            opposite_side = chr(ord(side) - 1)  # B -> A, D -> C, F -> E, H -> G
        return f"{opposite_side}{number}"
    return None


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


            # Get the opposite section of the current section
            opposite_section = get_opposite_section(section.name)

            try:
                left_section_latest_image = ImageList.objects.filter(section__name__in=[section, opposite_section], side="left").latest('date')
                right_section_latest_image = ImageList.objects.filter(section__name__in=[section, opposite_section], side="right").latest('date')
                front_latest_image = FrontView.objects.latest('date')

                time_perid_for_upload_image_timedelay = 1000000  # untis: seconds, default: 10s
                # Check LEFE image
                if now() - left_section_latest_image.date <= timedelta(seconds=time_perid_for_upload_image_timedelay):
                    left_image = left_section_latest_image
                else:
                    left_section_latest_image = None

                # Check RIGHT image
                if now() - right_section_latest_image.date <= timedelta(seconds=time_perid_for_upload_image_timedelay):
                    right_image = right_section_latest_image
                else:
                    right_section_latest_image = None

                # Check FRONT image
                if now() - front_latest_image.date <= timedelta(seconds=time_perid_for_upload_image_timedelay):
                    front_image = front_latest_image
                else:
                    front_latest_image = None

            except ImageList.DoesNotExist:
                print("No side images found.")
            except FrontView.DoesNotExist:
                print("No front images found.")


            # Only check if the section is legal, but do not store it in this table
            lidar_data = Lidar2D_ROS_data(
                lidar_model=lidar_model,
                ranges=ranges,
                create_time=now(),
                front_image=front_image,
                left_image=left_image,
                right_image=right_image
            )
            lidar_data.save()

            # print(f"id: {lidar_data.id}, {lidar_model = }, {section = }, {len(ranges) = }, left_image = {left_section_latest_image}, right_image = {right_section_latest_image}, front_image = {front_latest_image}")
            return Response({"message": "Data successfully saved."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Forward scarch
def obtain_side_image_based_on_lidar(lidar: Lidar2D_ROS_data) -> Tuple[Optional[ImageList], Optional[ImageList]]:
    left_image = lidar.left_image if lidar.left_image else None
    right_image = lidar.right_image if lidar.right_image else None

    return (left_image, right_image) # tuple type

# Backward search
def obtain_lidar_data_based_on_side_image(image: ImageList) -> Lidar2D_ROS_data:
    try:
        if image.side == "left":
            return ImageList.objects.get(id=image.id).lidar2d_left_set.all().latest('create_time')
        elif image.side == "right":
            return ImageList.objects.get(id=image.id).lidar2d_right_set.all().latest('create_time')
    except Lidar2D_ROS_data.DoesNotExist:
        return None

def obtain_front_image_based_on_lidar(lidar: Lidar2D_ROS_data) -> FrontView:
    return lidar.front_image if lidar.front_image else None
