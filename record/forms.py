from django import forms
from django.core.exceptions import ValidationError
from .models import Section, ImageList, FrontView

# class UploadFileForm(forms.Form):
#     name = forms.CharField(max_length=50, label="File name")
#     date = forms.DateTimeField(label="Upload date",required=False)
#     section = forms.CharField(max_length=10, label="Image upload to section")
#     image = forms.FileField(label="Image", required=False)

#     def check_section(self):
#         data = self.cleaned_data['section']
#         section_names = [ section.name for section in Section.objects.all()]
#         if data not in section_names:
#             raise ValidationError(_('Invalid section name'))
#         return data
    
class ImageListForm(forms.ModelForm):
    section = forms.ModelChoiceField(queryset=Section.objects.all(), to_field_name='name')
    def __init__(self, *args, **kwargs):
        super(ImageListForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['date'].required = False
        self.fields['focus'].required = False
    class Meta:
        model = ImageList
        fields = ['section', 'name', 'date', 'image', 'focus']

class FrontViewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FrontViewForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['date'].required = False
        self.fields['focus'].required = False
        
    class Meta:
        model = FrontView
        fields = '__all__'
