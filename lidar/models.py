import sys
from os import path

from django.db import models
from django.utils.timezone import now
from datetime import datetime

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from record.models import ImageList, FrontView, Section


class Scan(models.Model):
    name = models.CharField(max_length=100, default=str(datetime.now().strftime('%Y%m%d_%H%M%S')))
    date = models.DateTimeField('Date created', default=now)
    front_image = models.ForeignKey(FrontView, on_delete=models.CASCADE)
    left_image = models.ForeignKey(ImageList, on_delete=models.CASCADE, related_name='scan_left_images') # TODO: 應該要加上null=True
    right_image = models.ForeignKey(ImageList, on_delete=models.CASCADE, related_name='scan_right_images')
    points = models.JSONField()

    def __str__(self):
        return self.name + '_' + str(self.id)
    class Meta:
        ordering = ['-date']
        get_latest_by = "date"


# Store the lidar model name and its parameters
class Lidar2D_model(models.Model):
    model_name = models.CharField(max_length=100)
    create_time = models.DateTimeField('Time created', default=now)

    angle_min = models.FloatField()
    angle_max = models.FloatField()
    angle_increment = models.FloatField()
    range_min = models.FloatField()
    range_max = models.FloatField()

    def __str__(self):
        return self.model_name


# Store the lidar scan data (range)
class Lidar2D_ROS_data(models.Model):
    create_time = models.DateTimeField('Time created', default=now)
    lidar_model = models.ForeignKey(Lidar2D_model, on_delete=models.CASCADE)
    ranges = models.JSONField()

    front_image = models.ForeignKey(FrontView, on_delete=models.CASCADE)
    left_image = models.ForeignKey(ImageList, on_delete=models.CASCADE, related_name='lidar2d_ros_left_images')
    right_image = models.ForeignKey(ImageList, on_delete=models.CASCADE, related_name='lidar2d_ros_right_images')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    def __str__(self):
        return f"LaserScan {self.id} at {self.create_time}"

    class Meta:
        ordering = ['-create_time']
        get_latest_by = "create_time"