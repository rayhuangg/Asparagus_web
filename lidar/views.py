import math
import sys
from os import path
from datetime import timedelta
from typing import Tuple, Optional
import numpy as np

from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view


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
    if the current section is 'unspecified_right', the opposite section is 'unspecified_left'.
    '''
    if section_name[0] in 'ABCDEFGH':
        side = section_name[0]
        number = section_name[1:]
        if side in 'ACEG':
            opposite_side = chr(ord(side) + 1)  # A -> B, C -> D, E -> F, G -> H
        elif side in 'BDFH':
            opposite_side = chr(ord(side) - 1)  # B -> A, D -> C, F -> E, H -> G
        return f"{opposite_side}{number}"
    elif section_name == "unspecified_right":
        return "unspecified_left"
    elif section_name == "unspecified_left":
        return "unspecified_right"
    else:
        return None


class Lidar2dData(APIView):
    def post(self, request):
        serializer = Lidar2D_ROS_data_Serializer(data=request.data)

        if serializer.is_valid():
            lidar_model = serializer.validated_data['lidar_model']
            section = serializer.validated_data['section']
            ranges = serializer.validated_data['ranges']
            side = serializer.validated_data['side']
            left_image = None
            right_image = None
            front_image = None

            # Constants for determining lidar and image data are the same point or not, based on the time delay between them upload time.
            self.IMAGE_UPLOAD_TIME_DELAY_SECOND = 10  # units: seconds, default: 10s

            # DROXO spraying robot, install on the both side of the robot
            # Only find one side image, without considering the opposite side and front image
            if lidar_model.model_name == "RPLIDAR S2":
                if side == "left":
                    try:
                        left_section_latest_image = ImageList.objects.filter(section__name=section, side="left").latest('date')
                        left_image = self.check_left_image_timedelta(left_section_latest_image)
                    except ImageList.DoesNotExist:
                        print("No left side images found.")

                elif side == "right":
                    try:
                        right_section_latest_image = ImageList.objects.filter(section__name=section, side="right").latest('date')
                        right_image = self.check_right_image_timedelta(right_section_latest_image)
                    except ImageList.DoesNotExist:
                        print("No right side images found.")
                else:
                    print("Side must be either 'left' or 'right'.")
                    return Response("Side must be either 'left' or 'right'.", status=status.HTTP_400_BAD_REQUEST)

            # SSL Robot, install on center line of the robot.
            # Find the front, side, and the opposite side images
            elif lidar_model.model_name == "UST-05LX":
                # Get the opposite section of the current section
                opposite_section = get_opposite_section(section.name)
                try:
                    left_section_latest_image = ImageList.objects.filter(section__name__in=[section, opposite_section], side="left").latest('date')
                    right_section_latest_image = ImageList.objects.filter(section__name__in=[section, opposite_section], side="right").latest('date')
                    front_latest_image = FrontView.objects.latest('date')

                    left_image = self.check_left_image_timedelta(left_section_latest_image)
                    right_image = self.check_right_image_timedelta(right_section_latest_image)
                    front_image = self.check_front_image_timedelta(front_latest_image)

                except ImageList.DoesNotExist:
                    print("No side images found.")
                except FrontView.DoesNotExist:
                    print("No front images found.")

            else:
                print("Lidar model does not exist.")

            # Only check if the section is legal, but do not store it in this table
            lidar_data = Lidar2D_ROS_data(
                lidar_model=lidar_model,
                side=side,
                ranges=ranges,
                create_time=now(),
                front_image=front_image,
                left_image=left_image,
                right_image=right_image
            )

            lidar_data.save()
            return Response({"message": "Data successfully saved."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def check_front_image_timedelta(self, front_latest_image):
        return front_latest_image if now() - front_latest_image.date <= timedelta(seconds=self.IMAGE_UPLOAD_TIME_DELAY_SECOND) else None

    def check_right_image_timedelta(self, right_section_latest_image):
        return right_section_latest_image if now() - right_section_latest_image.date <= timedelta(seconds=self.IMAGE_UPLOAD_TIME_DELAY_SECOND) else None

    def check_left_image_timedelta(self, left_section_latest_image):
        return left_section_latest_image if now() - left_section_latest_image.date <= timedelta(seconds=self.IMAGE_UPLOAD_TIME_DELAY_SECOND) else None


# To RayBai, Forward search
def obtain_side_image_based_on_lidar(lidar: Lidar2D_ROS_data) -> Tuple[Optional[ImageList], Optional[ImageList]]:
    left_image = lidar.left_image if lidar.left_image else None
    right_image = lidar.right_image if lidar.right_image else None

    return (left_image, right_image) # tuple type

# To RayBai, Backward search
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


# To RayBai, Possible used in the future, if need to check the inf data is valid or not
def restore_numpy_inf_from_data(ranges) -> np.array:
    arr = np.array(ranges)
    arr[arr == 65.533] = np.inf
    arr[arr == -65.533] = -np.inf
    return arr


# To RayBai, sample query code for getting the lidar data
@api_view(['GET'])
def get_lidar_data_sample(request):
    try:
        # qury the latest lidar data
        lidar = Lidar2D_ROS_data.objects.latest()

        # query the specific lidar data based on the id
        # lidar = Lidar2D_ROS_data.objects.get(id=5)

        # query the latest lidar data based on the lidar model
        # lidar = Lidar2D_ROS_data.objects.filter(lidar_model__model_name="UST-05LX").latest()

    except Lidar2D_ROS_data.DoesNotExist:
        return Response({"error": "No Lidar data available"}, status=status.HTTP_404_NOT_FOUND)

    left_image = f"{lidar.left_image.name}-id{lidar.left_image.id}" if lidar.left_image else None
    right_image = f"{lidar.right_image.name}-id{lidar.right_image.id}" if lidar.right_image else None
    front_image = f"{lidar.front_image.name}-id{lidar.front_image.id}" if lidar.front_image else None
    side = lidar.side if lidar.side else None
    model = lidar.lidar_model
    range_data = lidar.ranges
    range_data_max = np.max(range_data)
    range_data_min = np.min(range_data)
    len_range_data = len(range_data)

    model_name = model.model_name
    model_create_time = model.create_time
    angle_min = model.angle_min
    angle_angle_increment = model.angle_increment
    range_min = model.range_min

    data = {
        "lidar_model_data": {
            "model_name": model_name,
            "model_create_time": model_create_time,
            "angle_min": angle_min,
            "angle_angle_increment": angle_angle_increment,
            "range_min": range_min
        },
        "left_image": left_image,
        "right_image": right_image,
        "front_image": front_image,
        "side": side,
        "range_data_max": range_data_max,
        "range_data_min": range_data_min,
        "len_range_data": len_range_data,

    }

    return Response(data, status=status.HTTP_200_OK)
