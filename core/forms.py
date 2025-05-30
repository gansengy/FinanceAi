from django import forms

class CheckUploadForm(forms.Form):
    image = forms.ImageField(label='Завантажити чек')
