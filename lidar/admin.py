from django.contrib import admin
from .models import Scan

# Register your models here.
class ScanAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name']}),
                 (None, {'fields': ['date']}),
                 (None, {'fields': ['left_image']}),
                 (None, {'fields': ['right_image']}),
                 (None, {'fields': ['points']})
                ]
admin.site.register(Scan, ScanAdmin)