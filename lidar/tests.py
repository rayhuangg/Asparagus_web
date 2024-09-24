import sys
from os import path

from django.test import Client, TestCase
from django.urls import reverse
from django.utils.timezone import now
from datetime import timedelta
from .models import Lidar2D_ROS_data, ImageList, FrontView

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from record.models import ImageList, FrontView

class TestLidar2dData(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('lidar2dData')
        self.lidar_model = "RPLIDAR S2"
        self.section = "A1"
        self.ranges = [1.0, 2.0, 3.0]
        self.side = "left"
        self.image_date = now() - timedelta(seconds=5)
        self.left_image = ImageList.objects.create(section=self.section, side="left", date=self.image_date)
        self.right_image = ImageList.objects.create(section=self.section, side="right", date=self.image_date)
        self.front_image = FrontView.objects.create(date=self.image_date)

    def test_post_valid_data(self):
        data = {
            "lidar_model": self.lidar_model,
            "section": self.section,
            "ranges": self.ranges,
            "side": self.side
        }
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lidar2D_ROS_data.objects.count(), 1)
        lidar_data = Lidar2D_ROS_data.objects.first()
        self.assertEqual(lidar_data.lidar_model, self.lidar_model)
        self.assertEqual(lidar_data.section, self.section)
        self.assertEqual(lidar_data.ranges, self.ranges)
        self.assertEqual(lidar_data.side, self.side)
        self.assertIsNotNone(lidar_data.left_image)
        self.assertIsNone(lidar_data.right_image)
        self.assertIsNone(lidar_data.front_image)

    def test_post_invalid_data(self):
        data = {
            "lidar_model": self.lidar_model,
            "section": self.section,
            "ranges": "invalid_ranges",
            "side": self.side
        }
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lidar2D_ROS_data.objects.count(), 0)

    def test_post_missing_data(self):
        data = {
            "lidar_model": self.lidar_model,
            "section": self.section,
            "side": self.side
        }
        response = self.client.post(self.url, data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Lidar2D_ROS_data.objects.count(), 0)