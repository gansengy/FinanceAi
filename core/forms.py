from django import forms
from django.utils import timezone
from .models import Transaction, Category


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва категорії'
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Іконка (емодзі)',
                'maxlength': '2'
            })
        }
        labels = {
            'name': 'Назва категорії',
            'icon': 'Іконка'
        }


class CheckUploadForm(forms.Form):
    image = forms.ImageField(label='Завантажити чек')


class TransactionForm(forms.ModelForm):
    created_at = forms.DateTimeField(
        label='Дата та час',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=False
    )

    class Meta:
        model = Transaction
        fields = ['name', 'price', 'category', 'created_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Назва товару'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ціна',
                'step': '0.01'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'name': 'Назва товару',
            'price': 'Ціна (грн)',
            'category': 'Категорія'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показувати тільки категорії витрат
        self.fields['category'].queryset = Category.objects.filter(is_income=False)

        # Встановити поточну дату як значення за замовчуванням
        if not self.instance.pk:
            self.initial['created_at'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
        elif self.instance and self.instance.pk:
            self.initial['created_at'] = self.instance.created_at.strftime('%Y-%m-%dT%H:%M')

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Якщо дата не вказана, використовуємо поточну
        if not self.cleaned_data.get('created_at'):
            instance.created_at = timezone.now()
        instance.transaction_type = 'expense'
        if commit:
            instance.save()
        return instance


class IncomeForm(forms.ModelForm):
    created_at = forms.DateTimeField(
        label='Дата та час',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=False
    )

    class Meta:
        model = Transaction
        fields = ['name', 'price', 'category', 'created_at']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Джерело прибутку'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Сума',
                'step': '0.01'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'name': 'Джерело прибутку',
            'price': 'Сума (грн)',
            'category': 'Категорія'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показувати тільки категорії прибутків
        self.fields['category'].queryset = Category.objects.filter(is_income=True)

        # Встановити поточну дату як значення за замовчуванням
        if not self.instance.pk:
            self.initial['created_at'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
        elif self.instance and self.instance.pk:
            self.initial['created_at'] = self.instance.created_at.strftime('%Y-%m-%dT%H:%M')

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Якщо дата не вказана, використовуємо поточну
        if not self.cleaned_data.get('created_at'):
            instance.created_at = timezone.now()
        instance.transaction_type = 'income'
        if commit:
            instance.save()
        return instance