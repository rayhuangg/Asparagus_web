from django.db import models
from django.utils.timezone import now
from datetime import datetime

# Create your models here.
class Section(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateTimeField('Date created', default=now)
    # date.editable = True

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['date']

class ImageList(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    def uppath(instance, fname):
        path = 'record/img/' + instance.section.name + '/' +  fname
        return path

    name = models.CharField(max_length=100, default=str(datetime.now().strftime('%Y%m%d_%H%M%S')))
    date = models.DateTimeField(default=now)
    # date.editable = True
    image = models.ImageField(upload_to=uppath)

    def __str__(self):
        return self.name + '_' + str(self.id)

    class Meta:
        ordering = ['-date']
        get_latest_by = "date"

class FrontView(models.Model):
    name = models.CharField(max_length=100, default=str(datetime.now().strftime('%Y%m%d_%H%M%S')))
    date = models.DateTimeField(default=now)
    image = models.ImageField(upload_to='record/front')

    def __str__(self):
        return self.name

    class Meta:
        get_latest_by = "date"