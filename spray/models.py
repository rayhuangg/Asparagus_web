from django.db import models

# Create your models here.


class PesticideList(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'spray'

    def __str__(self):
        return self.name

class SprayExperimentRecord(models.Model):
    LOCATION_CHOICES = [
        ("Yizhu_Branch_Station", "MOA Yizhu branch station"),
        ("YanShuo", "Yan Shuo's greenhouse")
    ]
    experiment_id = models.AutoField(primary_key=True)
    location = models.CharField(max_length=255, choices=LOCATION_CHOICES)
    pesticide = models.ManyToManyField(PesticideList)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    class Meta:
        app_label = 'spray'

    def __str__(self):
        pesticides = ', '.join([str(pesticide) for pesticide in self.pesticide.all()])
        return f"{self.get_location_display()} - {pesticides} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
