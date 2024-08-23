from django.contrib import admin
from .models import SprayExperimentRecord, FertilizerList


class FertilizerListAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')


class SprayExperimentRecordAdmin(admin.ModelAdmin):
    list_display = ('experiment_id', 'location', 'greenhouse', 'start_time', 'end_time', 'display_fertilizers', 'fertilizer_total_amount')
    list_filter = ('location', 'greenhouse')
    search_fields = ('location', 'greenhouse')
    date_hierarchy = 'start_time'
    ordering = ('-start_time',)

    def display_fertilizers(self, obj):
        return ", ".join([fertilizer.name for fertilizer in obj.fertilizer.all()])
    display_fertilizers.short_description = 'Fertilizers'

admin.site.register(FertilizerList, FertilizerListAdmin)
admin.site.register(SprayExperimentRecord, SprayExperimentRecordAdmin)