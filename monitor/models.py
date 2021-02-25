from django.db import models
from django.utils.timezone import now
from datetime import datetime
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from record.models import ImageList

class Demo(models.Model):
    name = models.CharField(max_length=100, default=str(datetime.now().strftime('%Y%m%d_%H%M%S')))
    date = models.DateTimeField(default=now)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date']
        get_latest_by = 'date'

# Create your models here.
class ResultList(models.Model):
    name = models.CharField(max_length=100, default=str(datetime.now().strftime('%Y%m%d_%H%M%S')))
    date = models.DateTimeField(default=now)
    image = models.ForeignKey(ImageList, on_delete=models.CASCADE)
    demo = models.ForeignKey(Demo, on_delete=models.CASCADE, default=0)

    # @classmethod
    # def create(cls, name, date, image_id):
    #     image = ImageList.objects.filter(section_id=image_id).latest().id
    #     resultlist = cls(name=name, date=date, image=image)
    #     return resultlist

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date']
        get_latest_by = 'date'

class Instance(models.Model):
    predicted_class = models.CharField(max_length=100, choices=[('clump', 'Clump'), ('stalk', 'Stalk'), ('spear', 'Spear'), ('bar', 'Bar')])
    score = models.FloatField(default=0)
    bbox_xmin = models.IntegerField(default=0)
    bbox_ymin = models.IntegerField(default=0)
    bbox_xmax = models.IntegerField(default=0)
    bbox_ymax = models.IntegerField(default=0)
    mask = models.JSONField()
    height = models.FloatField(default=0)
    width = models.FloatField(default=0)
    resultlist = models.ForeignKey(ResultList, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add = True, auto_now = False)

    # @classmethod
    # def create(cls, predicted_class, score, bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax, mask, resultlist):
    #     class_id = {1: 'clump', 2: 'stalk' , 3: 'spear'}
    #     instance = cls(predicted_class=class_id[predicted_class], score=score, bbox_xmin=bbox_xmin, bbox_ymin=bbox_ymin, bbox_xmax=bbox_xmax, bbox_ymax=bbox_ymax, mask=mask, resultlist_id=ResultList.objects.all().latest())
    #     return instance

    def __str__(self):
        return self.predicted_class

    class Meta:
        ordering = ['created']
        get_latest_by = 'created'