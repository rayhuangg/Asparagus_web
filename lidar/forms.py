from django import forms
from datetime import datetime
from django.utils.timezone import now

from django.core.exceptions import ValidationError
import sys
from os import path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from record.models import Section, ImageList
from .models import Scan

# class ScanForm(forms.ModelForm):
#     left_image = forms.ModelChoiceField(queryset=ImageList.objects.all(), to_field_name='name')
#     right_image = forms.ModelChoiceField(queryset=ImageList.objects.all(), to_field_name='name')
#     def __init__(self, *args, **kwargs):
#             super(ScanForm, self).__init__(*args, **kwargs)
#             self.fields['name'].required = False
#             self.fields['date'].required = False
#     class Meta:
#         model = Scan
#         fields = '__all__'

class ScanForm(forms.Form):
    name = forms.CharField(label='Name of this scan', max_length=100, initial=str(datetime.now().strftime('%Y%m%d_%H%M%S')), required=False)
    date = forms.DateTimeField(label='Date created', initial=now, required=False)
    left_section = forms.ModelChoiceField(queryset=Section.objects.all(), to_field_name='name', required=False)
    right_section = forms.ModelChoiceField(queryset=Section.objects.all(), to_field_name='name', required=False)
    points = forms.JSONField()