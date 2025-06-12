from django.db import migrations


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')

    # Перевіряємо, чи модель має поле is_default
    model_fields = [f.name for f in Category._meta.get_fields()]
    has_is_default = 'is_default' in model_fields

    default_categories = [
        {'name': 'їжа', 'icon': '🍔'},
        {'name': 'напої', 'icon': '🥤'},
        {'name': 'алкоголь', 'icon': '🍺'},
        {'name': 'одяг', 'icon': '👕'},
        {'name': 'побут', 'icon': '🏠'},
        {'name': 'медицина', 'icon': '💊'},
        {'name': 'техніка', 'icon': '💻'},
        {'name': 'транспорт', 'icon': '🚗'},
        {'name': 'розваги', 'icon': '🎮'},
        {'name': 'інше', 'icon': '📦'},
    ]

    for cat in default_categories:
        defaults = {'icon': cat['icon']}
        if has_is_default:
            defaults['is_default'] = True

        Category.objects.get_or_create(
            name=cat['name'],
            defaults=defaults
        )


def reverse_default_categories(apps, schema_editor):
    Category = apps.get_model('core', 'Category')
    default_names = ['їжа', 'напої', 'алкоголь', 'одяг', 'побут',
                     'медицина', 'техніка', 'транспорт', 'розваги', 'інше']
    Category.objects.filter(name__in=default_names).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_category_is_default'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, reverse_default_categories),
    ]