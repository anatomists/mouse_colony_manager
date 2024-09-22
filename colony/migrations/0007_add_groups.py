from django.db import migrations
from django.contrib.auth.models import Group

def create_groups(apps, schema_editor):
    Group.objects.get_or_create(name='Mice Colony Manager')
    Group.objects.get_or_create(name='Regular User')

class Migration(migrations.Migration):

    dependencies = [
        ('colony', '0006_mouse_is_sacrificed'),  # replace with your last migration
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]
