from django.contrib import admin
from django.db import models
from .models import Instance, ResultList, Demo

class AdminImageWidget(admin.widgets.AdminFileWidget):
    """Admin widget for showing clickable thumbnail of Image file fields"""

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        if value and getattr(value, 'url', None):
            html = format_html('<a href="{0}" target="_blank"><img src="{0}" alt="{1}" width="150" height="150" style="object-fit: contain;"/></a>', value.url, str(value)) + html
        return html

class InstanceInline(admin.TabularInline):
    model = Instance
    exclude = ['created',]
    extra = 0

class ResultListAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name']}),
                 (None, {'fields': ['date']}),
                 (None, {'fields': ['image']})
                 ]
    inlines = [InstanceInline,]
    list_display = ('name', 'date', 'section', 'id', 'id_of_related_image')

    def section(self, obj):
        return obj.image.section.name

    def id(self, obj):
        return obj.id

    def id_of_related_image(self, obj):
        return obj.image.id

class ResultListInline(admin.TabularInline):
    model = ResultList
    extra = 0

class DemoAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name']}),
                 (None, {'fields': ['date']}),
                 (None, {'fields': ['source']})
                 ]
    inlines = [ResultListInline,]

    list_display = ('name', 'date', 'id', 'number_of_detections')

    def number_of_detections(self, obj):
        return len(ResultList.objects.filter(demo__id=obj.id))

admin.site.register(ResultList, ResultListAdmin)
admin.site.register(Demo, DemoAdmin)