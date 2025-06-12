# Створіть новий файл міграції, наприклад: 0004_add_income_categories.py

from django.db import migrations


def create_income_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')

    income_categories = [
        {'name': 'робота', 'icon': '💼', 'is_income': True, 'is_default': True},
        {'name': 'інвестиції', 'icon': '📈', 'is_income': True, 'is_default': True},
        {'name': 'чайові', 'icon': '💵', 'is_income': True, 'is_default': True},
        {'name': 'підробіток', 'icon': '💰', 'is_income': True, 'is_default': True},
        {'name': 'інше (прибуток)', 'icon': '💸', 'is_income': True, 'is_default': True},
    ]

    for cat in income_categories:
        Category.objects.get_or_create(
            name=cat['name'],
            defaults={
                'icon': cat['icon'],
                'is_income': cat['is_income'],
                'is_default': cat['is_default']
            }
        )


def reverse_income_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    income_names = ['робота', 'інвестиції', 'чайові', 'підробіток', 'інше (прибуток)']
    Category.objects.filter(name__in=income_names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_category_is_income_transaction_transaction_type_and_more'),  # Змініть на вашу попередню міграцію
    ]

    operations = [
        migrations.RunPython(create_income_categories, reverse_income_categories),
    ]