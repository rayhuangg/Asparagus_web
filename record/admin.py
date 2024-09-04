from django.contrib import admin
from django.db import models
from django.utils.html import mark_safe, format_html

from .models import Section, ImageList, FrontView
# Register your models here.

admin.site.site_header = "Asparagus"

class AdminImageWidget(admin.widgets.AdminFileWidget):
    """Admin widget for showing clickable thumbnail of Image file fields"""

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        if value and getattr(value, 'url', None):
            html = format_html('<a href="{0}" target="_blank"><img src="{0}" alt="{1}" width="150" height="150" style="object-fit: contain;"/></a>', value.url, str(value)) + html
        return html

class ImageListInline(admin.TabularInline):
    model = ImageList
    fields = ('name', 'date', 'id', 'image', "side")
    extra = 0
    formfield_overrides = {
        models.ImageField: {'widget': AdminImageWidget}
    }

class ImageListAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'section', 'id', 'preview')

    def section(self, obj):
        return obj.section.name

    def id(self, obj):
        return obj.id

    def preview(self,obj):
        return format_html('<img src="{0}" style="width: 200px; height: auto;" />'.format(obj.image.url))

class SectionAdmin(admin.ModelAdmin):
    fieldsets = [(None, {'fields': ['name']}),
                 (None, {'fields': ['date']}),
                 ]
    inlines = [ImageListInline,]
    list_display = ('name', 'date', 'number_of_images', 'preview_of_latest_image')

    def number_of_images(self, obj):
        return len(ImageList.objects.filter(section__name=obj.name))

    def preview_of_latest_image(self, obj):
        return format_html('<img src="{0}" style="width: 200px; height: auto;" />'.format(ImageList.objects.filter(section__name=obj.name).latest().image.url))

class FrontViewAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'id', 'preview')

    def id(self, obj):
        return obj.id

    def preview(self,obj):
        return format_html('<img src="{0}" style="width: 200px; height: auto;" />'.format(obj.image.url))

# admin.site.register(ImageList)
admin.site.register(FrontView, FrontViewAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(ImageList, ImageListAdmin)