from django.contrib import admin
from .models import SprayExperimentRecord, FertilizerList, FertilizerUsage


class FertilizerListAdmin(admin.ModelAdmin):
    list_display = ('name', 'id')


class FertilizerUsageInline(admin.TabularInline):
    model = FertilizerUsage
    extra = 1  # Show extra rows for adding fertilizer usage directly in the experiment record page
    fields = ('fertilizer', 'amount')


class SprayExperimentRecordAdmin(admin.ModelAdmin):
    list_display = ('experiment_id', 'location', 'greenhouse', 'start_time', 'end_time', 'total_water_used', 'get_fertilizer_usages', 'note')
    list_filter = ('location', 'greenhouse')
    search_fields = ('location', 'greenhouse')
    date_hierarchy = 'start_time'
    ordering = ('-start_time',)

    # Inline allows you to edit FertilizerUsage directly in the SprayExperimentRecord admin page
    inlines = [FertilizerUsageInline]

    def get_fertilizer_usages(self, obj):
        return obj.get_fertilizer_usage()
    get_fertilizer_usages.short_description = 'Fertilizer Usages'

admin.site.register(FertilizerList, FertilizerListAdmin)
admin.site.register(SprayExperimentRecord, SprayExperimentRecordAdmin)