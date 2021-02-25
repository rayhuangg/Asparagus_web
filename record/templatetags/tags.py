from django import template

register = template.Library()

@register.filter
def data_type(value):
    return type(value)