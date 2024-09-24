import sys
from os import path

from django.db import models
from django.utils.timezone import now
from datetime import datetime

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from record.models import ImageList, FrontView, Section


# Old version, only store the scan points without any ROS format
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

    class Meta:
        # make admin page readable, cause Django will auto add space betweed Upper case word
        verbose_name = "Lidar2D ROS model"
        verbose_name_plural = "Lidar2D ROS models"


# New version, Store the lidar scan data (range)
class Lidar2D_ROS_data(models.Model):
    create_time = models.DateTimeField('Time created', default=now)
    lidar_model = models.ForeignKey(Lidar2D_model, on_delete=models.CASCADE)
    ranges = models.JSONField()
    side = models.CharField(max_length=5, choices=[('left', 'left'), ('right', 'right')], null=True) # only for DROXO used

    left_image = models.ForeignKey(
        ImageList, on_delete=models.SET_NULL, null=True, blank=True, related_name='lidar2d_left_set'
    )
    right_image = models.ForeignKey(
        ImageList, on_delete=models.SET_NULL, null=True, blank=True, related_name='lidar2d_right_set'
    )
    front_image = models.ForeignKey(
        FrontView, on_delete=models.SET_NULL, null=True, blank=True, related_name='lidar2d_front_set'
    )

    def __str__(self):
        return f"{self.lidar_model} - id {self.id} - upload at {self.create_time.astimezone().strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['-create_time']
        get_latest_by = "create_time"

        # make admin page readable, cause Django will auto add space betweed Upper case word
        verbose_name = "Lidar2D ROS Data"
        verbose_name_plural = "Lidar2D ROS Data"