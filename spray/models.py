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
    start_time = models.DateTimeField(default=now)
    end_time = models.DateTimeField(null=True, blank=True)
    total_water_used = models.FloatField(null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    class Meta:
        app_label = 'spray'

    def __str__(self):
        return f"{self.location} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def get_fertilizer_usage(self):
        usages = FertilizerUsage.objects.filter(experiment=self)
        return ', '.join(f"{usage.fertilizer.name}: {usage.amount}g" for usage in usages)


class FertilizerUsage(models.Model):
    experiment = models.ForeignKey(SprayExperimentRecord, on_delete=models.CASCADE)
    fertilizer = models.ForeignKey(FertilizerList, on_delete=models.CASCADE)
    amount = models.FloatField()

    class Meta:
        app_label = 'spray'

    def __str__(self):
        return f"{self.fertilizer.name} - {self.amount}g"