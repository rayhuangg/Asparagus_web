from django.contrib import admin
from .models import SprayExperimentRecord, FertilizerList


admin.site.register(FertilizerList)



class SprayExperimentRecordAdmin(admin.ModelAdmin):
    list_display = ('experiment_id', 'location', 'greenhouse', 'start_time', 'end_time', 'fertilizer_total_amount')
    list_filter = ('location', 'greenhouse')
    search_fields = ('location', 'greenhouse')
    date_hierarchy = 'start_time'
    ordering = ('-start_time',)
    filter_horizontal = ('fertilizer',)  # 這需要 'fertilizer' 是 ManyToManyField

admin.site.register(SprayExperimentRecord, SprayExperimentRecordAdmin)