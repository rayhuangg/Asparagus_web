from django.db import models
from django.utils.timezone import now


class FertilizerList(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'spray'

    def __str__(self):
        return self.name


class SprayExperimentRecord(models.Model):
    experiment_id = models.AutoField(primary_key=True)
    location = models.CharField(max_length=255)
    greenhouse = models.CharField(max_length=255)
    fertilizer = models.ManyToManyField(FertilizerList)
    start_time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(null=True, blank=True)
    fertilizer_total_amount = models.FloatField(null=True, blank=True)

    class Meta:
        app_label = 'spray'

    def __str__(self):
        pesticides = ', '.join(str(pesticide) for pesticide in self.fertilizer.all())
        return f"{self.location} - {pesticides} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
