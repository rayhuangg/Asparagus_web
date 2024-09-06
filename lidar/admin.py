from django.contrib import admin
from .models import Scan, Lidar2D_model, Lidar2D_ROS_data

# Register your models here.
class ScanAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name']}),
                 (None, {'fields': ['date']}),
                 (None, {'fields': ['front_image']}),
                 (None, {'fields': ['left_image']}),
                 (None, {'fields': ['right_image']}),
                 (None, {'fields': ['points']})
                ]

class Lidar2D_modelAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['model_name']}),
                 (None, {'fields': ['create_time']}),
                 (None, {'fields': ['angle_min']}),
                 (None, {'fields': ['angle_max']}),
                 (None, {'fields': ['angle_increment']}),
                 (None, {'fields': ['range_min']}),
                 (None, {'fields': ['range_max']})
                ]

class Lidar2D_ROS_dataAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['create_time']}),
                 (None, {'fields': ['lidar_model']}),
                 (None, {'fields': ['ranges']}),
                 (None, {'fields': ['front_image']}),
                 (None, {'fields': ['left_image']}),
                 (None, {'fields': ['right_image']}),
                 (None, {'fields': ['section']})
                ]

admin.site.register(Scan, ScanAdmin)
admin.site.register(Lidar2D_model, Lidar2D_modelAdmin)
admin.site.register(Lidar2D_ROS_data, Lidar2D_ROS_dataAdmin)