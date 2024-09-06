from django import forms
from django.core.exceptions import ValidationError
from .models import Section, ImageList, FrontView


class ImageListForm(forms.ModelForm):
    section = forms.ModelChoiceField(queryset=Section.objects.all(), to_field_name='name')
    def __init__(self, *args, **kwargs):
        super(ImageListForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['date'].required = False

    class Meta:
        model = ImageList
        fields = ['section', 'name', 'date', 'image', 'side']
    

class FrontViewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FrontViewForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['date'].required = False

    class Meta:
        model = FrontView
        fields = '__all__'
