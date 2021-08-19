from django.db import models
from django.utils.timezone import now
from datetime import datetime
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from record.models import ImageList, FrontView

class Scan(models.Model):
    name = models.CharField(max_length=100, default=str(datetime.now().strftime('%Y%m%d_%H%M%S')))
    date = models.DateTimeField('Date created', default=now)
    front_image = models.ForeignKey(FrontView, on_delete=models.CASCADE)
    left_image = models.ForeignKey(ImageList, on_delete=models.CASCADE, related_name='image_from_left_side')
    right_image = models.ForeignKey(ImageList, on_delete=models.CASCADE, related_name='image_from_right_side')
    points = models.JSONField()
    def __str__(self):
        return self.name + '_' + str(self.id)
    class Meta:
        ordering = ['-date']
        get_latest_by = "date"